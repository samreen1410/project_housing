// Animates a dollar figure counting up like a mechanical adding machine,
// instead of just snapping to the final number.
function animateMoney(el, targetValue, duration = 650) {
  const start = performance.now();
  const from = 0;

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // ease-out cubic — fast start, gentle settle, like a real tally
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = from + (targetValue - from) * eased;
    el.textContent = money(current);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
