// A field of ambient twinkling stars that also directly react to the
// cursor: nearby stars brighten and grow noticeably as you move through
// them, then ease back. Combines a calm ambient scene with a clearly
// interactive, direct effect (the earlier whole-page parallax was too
// subtle to register). Sits behind everything, never intercepts clicks.

(function () {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  const DENSITY = 9000;       // px^2 per star — lower = more stars
  const BASE_RADIUS = 1.1;
  const MAX_RADIUS = 4.5;
  const INFLUENCE = 160;      // px — how far the cursor's glow reaches

  let width, height, stars;
  let mouse = { x: -9999, y: -9999 };

  function buildStars() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    const count = Math.round((width * height) / DENSITY);

    stars = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      r: BASE_RADIUS,
      twinkleSpeed: 0.5 + Math.random() * 1.3,
      twinklePhase: Math.random() * Math.PI * 2,
    }));
  }

  function draw(time) {
    ctx.clearRect(0, 0, width, height);

    for (const s of stars) {
      const dx = s.x - mouse.x;
      const dy = s.y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const targetR = dist < INFLUENCE
        ? BASE_RADIUS + (MAX_RADIUS - BASE_RADIUS) * (1 - dist / INFLUENCE)
        : BASE_RADIUS;
      s.r += (targetR - s.r) * 0.18;

      const ambientTwinkle = 0.35 + 0.5 * (0.5 + 0.5 * Math.sin(time * 0.001 * s.twinkleSpeed + s.twinklePhase));
      const proximityBoost = Math.max(0, (s.r - BASE_RADIUS) / (MAX_RADIUS - BASE_RADIUS));
      const alpha = Math.min(1, ambientTwinkle + proximityBoost * 0.8);

      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = proximityBoost > 0.08
        ? `rgba(45, 212, 191, ${alpha})`   // near cursor: teal glow
        : `rgba(238, 242, 246, ${alpha})`; // ambient: soft white
      ctx.fill();
    }

    requestAnimationFrame(draw);
  }

  function drawStatic() {
    ctx.clearRect(0, 0, width, height);
    for (const s of stars) {
      ctx.beginPath();
      ctx.arc(s.x, s.y, BASE_RADIUS, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(238, 242, 246, 0.55)";
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
    buildStars();
    if (prefersReducedMotion) drawStatic();
  });

  buildStars();
  if (prefersReducedMotion) {
    drawStatic();
  } else {
    requestAnimationFrame(draw);
  }
})();
