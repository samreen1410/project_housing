// Masthead behaviour shared by every page:
//   1. Injects the navigation tabs into <div id="site-nav"></div> and
//      highlights whichever tab matches the current file name.
//   2. Makes the page title react to the cursor (setupTitleEffect, below).

function renderNav() {
    const navHost = document.getElementById("site-nav");
    if (!navHost) return;

    const currentPage = window.location.pathname.split("/").pop() || "index.html";

    const links = [
        { href: "index.html", label: "Home" },
        { href: "explorer.html", label: "Explore" },
        { href: "calculator.html", label: "Calculate" },
        { href: "recommender.html", label: "Recommend" },
    ];

    navHost.innerHTML = links
        .map(link => {
            const isActive = link.href === currentPage;
            return `<a href="${link.href}" class="${isActive ? "active" : ""}">${link.label}</a>`;
        })
        .join("");
}

document.addEventListener("DOMContentLoaded", renderNav);

// ---------- Title effect ----------
// A bright highlight follows the mouse across the title lettering, and the
// title tilts very slightly toward the cursor. Purely decorative. It is
// skipped for anyone who prefers reduced motion and on touch screens, and it
// lives in its own listener so it can never get in the way of the navigation.

function setupTitleEffect() {
    const masthead = document.querySelector(".masthead");
    const title = document.querySelector(".masthead h1");
    if (!masthead || !title) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (window.matchMedia("(hover: none)").matches) return;

    const OFFSCREEN_X = -40; // percent; keeps the highlight hidden when idle

    let targetX = OFFSCREEN_X, targetY = 50, curX = OFFSCREEN_X, curY = 50;
    let targetTiltX = 0, targetTiltY = 0, curTiltX = 0, curTiltY = 0;
    let frame = null;

    function tick() {
        curX += (targetX - curX) * 0.14;
        curY += (targetY - curY) * 0.14;
        curTiltX += (targetTiltX - curTiltX) * 0.1;
        curTiltY += (targetTiltY - curTiltY) * 0.1;

        title.style.setProperty("--mx", curX.toFixed(2) + "%");
        title.style.setProperty("--my", curY.toFixed(2) + "%");
        title.style.transform =
            `perspective(900px) rotateX(${curTiltX.toFixed(2)}deg) rotateY(${curTiltY.toFixed(2)}deg)`;

        const settled =
            Math.abs(targetX - curX) < 0.05 && Math.abs(targetY - curY) < 0.05 &&
            Math.abs(targetTiltX - curTiltX) < 0.01 && Math.abs(targetTiltY - curTiltY) < 0.01;

        frame = settled ? null : requestAnimationFrame(tick);
    }

    function wake() {
        if (!frame) frame = requestAnimationFrame(tick);
    }

    masthead.addEventListener("mousemove", (e) => {
        const t = title.getBoundingClientRect();
        const m = masthead.getBoundingClientRect();

        targetX = ((e.clientX - t.left) / t.width) * 100;
        targetY = ((e.clientY - t.top) / t.height) * 100;

        targetTiltY = ((e.clientX - (m.left + m.width / 2)) / (m.width / 2)) * 5;
        targetTiltX = -((e.clientY - (m.top + m.height / 2)) / (m.height / 2)) * 4;
        wake();
    });

    masthead.addEventListener("mouseleave", () => {
        targetX = OFFSCREEN_X;
        targetY = 50;
        targetTiltX = 0;
        targetTiltY = 0;
        wake();
    });
}

document.addEventListener("DOMContentLoaded", setupTitleEffect);