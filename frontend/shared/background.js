// A faint grid of dots, like graph/ledger paper, that gently brightens
// and grows near the cursor. Purely decorative, sits behind everything,
// and never intercepts clicks (see #bg-canvas { pointer-events: none } ).

(function () {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  const SPACING = 34;
  const BASE_RADIUS = 1.4;
  const MAX_RADIUS = 4.2;
  const INFLUENCE = 130; // px — how far the cursor's glow reaches

  let width, height, points;
  let mouse = { x: -9999, y: -9999 };

  function buildGrid() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    points = [];
    for (let x = SPACING / 2; x < width; x += SPACING) {
      for (let y = SPACING / 2; y < height; y += SPACING) {
        points.push({ x, y, r: BASE_RADIUS });
      }
    }
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    for (const p of points) {
      const dx = p.x - mouse.x;
      const dy = p.y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const targetR = dist < INFLUENCE
        ? BASE_RADIUS + (MAX_RADIUS - BASE_RADIUS) * (1 - dist / INFLUENCE)
        : BASE_RADIUS;

      // ease toward the target radius each frame for a smooth glow
      p.r += (targetR - p.r) * 0.15;

      const brightness = (p.r - BASE_RADIUS) / (MAX_RADIUS - BASE_RADIUS);
      const alpha = 0.10 + brightness * 0.45;
      const green = brightness > 0.05;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = green
        ? `rgba(47, 107, 52, ${alpha})`
        : `rgba(74, 90, 67, ${alpha})`;
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }

  function drawStatic() {
    // Reduced-motion fallback: a plain, non-reactive dot grid, no rAF loop.
    ctx.clearRect(0, 0, width, height);
    for (const p of points) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, BASE_RADIUS, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(74, 90, 67, 0.12)";
      ctx.fill();
    }
  }

  window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });
  window.addEventListener("mouseleave", () => {
    mouse.x = -9999;
    mouse.y = -9999;
  });
  window.addEventListener("resize", () => {
    buildGrid();
    if (prefersReducedMotion) drawStatic();
  });

  buildGrid();
  if (prefersReducedMotion) {
    drawStatic();
  } else {
    requestAnimationFrame(draw);
  }
})();
