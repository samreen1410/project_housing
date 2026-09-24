// Injects the ledger-tab navigation into <div id="site-nav"></div> on every
// page, and highlights whichever tab matches the current file name.

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
