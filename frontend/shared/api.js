// Shared across every page.
//
// While you develop locally this talks to your own backend. Once the site
// is live it talks to the deployed backend instead, so nothing needs to be
// toggled by hand.
//
// IMPORTANT: after deploying the backend (for example on Render), replace
// the placeholder below with its real URL. It looks like
// "https://your-service-name.onrender.com" with no slash at the end.
const DEPLOYED_API_BASE = "https://project-housing.onrender.com";

const IS_LOCAL = ["localhost", "127.0.0.1", ""].includes(window.location.hostname);
const API_BASE = IS_LOCAL ? "http://127.0.0.1:8000" : DEPLOYED_API_BASE;
const API_NOT_CONFIGURED = !IS_LOCAL && DEPLOYED_API_BASE.includes("REPLACE-WITH");

// ---------- Waking up a sleeping server ----------
// Free hosting puts the backend to sleep after a quiet spell, and the first
// request afterward can take up to a minute. Instead of showing an error,
// requests to the backend are retried for a while and a small banner
// explains what is happening. Every page gets this automatically because
// fetch is wrapped here, so no other file needs to change.

let wakeWaiters = 0;
let wakeBannerEl = null;

function ensureWakeBanner() {
    if (wakeBannerEl) return wakeBannerEl;

    const style = document.createElement("style");
    style.textContent = `
    .wake-banner {
      position: fixed; left: 50%; bottom: 24px; z-index: 9999;
      transform: translate(-50%, 20px); opacity: 0; pointer-events: none;
      display: flex; align-items: center; gap: 12px;
      padding: 12px 18px; border-radius: 999px;
      background: #223754; color: #eef2f6; border: 1px solid #2c3e58;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      font: 500 0.85rem 'Inter', sans-serif;
      max-width: calc(100vw - 32px);
      transition: opacity 0.25s ease, transform 0.25s ease;
    }
    .wake-banner.show { opacity: 1; transform: translate(-50%, 0); }
    .wake-spinner {
      width: 16px; height: 16px; flex-shrink: 0; border-radius: 50%;
      border: 2px solid rgba(45, 212, 191, 0.25); border-top-color: #2dd4bf;
      animation: wakeSpin 0.8s linear infinite;
    }
    @keyframes wakeSpin { to { transform: rotate(360deg); } }
  `;
    document.head.appendChild(style);

    wakeBannerEl = document.createElement("div");
    wakeBannerEl.className = "wake-banner";
    wakeBannerEl.setAttribute("role", "status");
    wakeBannerEl.innerHTML =
        '<span class="wake-spinner"></span>' +
        "<span>Waking up the server. The first visit after a quiet spell can take up to a minute.</span>";
    document.body.appendChild(wakeBannerEl);
    return wakeBannerEl;
}

function showWakeBanner() {
    wakeWaiters += 1;
    ensureWakeBanner().classList.add("show");
}

function hideWakeBanner() {
    wakeWaiters = Math.max(0, wakeWaiters - 1);
    if (wakeWaiters === 0 && wakeBannerEl) wakeBannerEl.classList.remove("show");
}

const nativeFetch = window.fetch.bind(window);

async function fetchWithWake(url, init) {
    if (API_NOT_CONFIGURED) throw new Error("The backend URL has not been set yet.");

    // Locally, fail fast. If the backend is off there is nothing to wait for.
    if (IS_LOCAL) return nativeFetch(url, init);

    const MAX_ATTEMPTS = 8;
    const ATTEMPT_TIMEOUT_MS = 20000;
    const RETRY_DELAY_MS = 3000;
    const RETRYABLE_STATUSES = [502, 503, 504];

    let bannerShown = false;
    const slowTimer = setTimeout(() => {
        // Each request registers with the banner at most once, whichever of
        // the two paths (slow first attempt, or a failed attempt) gets there first.
        if (!bannerShown) {
            bannerShown = true;
            showWakeBanner();
        }
    }, 2500);

    try {
        let lastError;
        for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), ATTEMPT_TIMEOUT_MS);
            try {
                const res = await nativeFetch(url, { ...init, signal: controller.signal });
                clearTimeout(timeout);
                if (!RETRYABLE_STATUSES.includes(res.status)) return res;
                lastError = new Error("The server returned status " + res.status);
            } catch (err) {
                clearTimeout(timeout);
                lastError = err;
            }

            if (attempt < MAX_ATTEMPTS) {
                if (!bannerShown) {
                    bannerShown = true;
                    showWakeBanner();
                }
                await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
            }
        }
        throw lastError || new Error("The server did not respond.");
    } finally {
        clearTimeout(slowTimer);
        if (bannerShown) hideWakeBanner();
    }
}

// Only requests to our own backend get the retry behavior. Everything else
// goes through the browser's normal fetch untouched.
window.fetch = function (input, init) {
    if (typeof input === "string" && input.startsWith(API_BASE)) {
        return fetchWithWake(input, init);
    }
    return nativeFetch(input, init);
};

// Text to show when the backend cannot be reached at all.
function backendErrorMessage() {
    if (IS_LOCAL) {
        return "The backend is not running. Start it with uvicorn in the backend folder, then refresh.";
    }
    if (API_NOT_CONFIGURED) {
        return "This site is not connected to its server yet.";
    }
    return "The server did not respond. Please wait a moment and try again.";
}

async function fetchRegions() {
    const res = await fetch(`${API_BASE}/regions/`);
    if (!res.ok) throw new Error("Could not reach the regions endpoint");
    return res.json();
}

async function fetchTransitPlans() {
    const res = await fetch(`${API_BASE}/transit-fares/`);
    if (!res.ok) throw new Error("Could not reach the transit-fares endpoint");
    return res.json();
}

function money(value) {
    return "$" + Number(value).toLocaleString("en-CA", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}