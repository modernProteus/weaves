// stagger the draft cells so the strip threads itself once on load
document.querySelectorAll(".cell").forEach((c, i) => {
  c.style.animationDelay = (i * 34) + "ms";
});

const box = document.getElementById("replies");

if (box) {
  const title = box.dataset.title;
  const to = (box.dataset.replyTo || "").trim();
  const said = document.getElementById("said");

  box.querySelectorAll(".reply").forEach(btn => {
    const msg = `${btn.dataset.msg} — re: ${title}`;

    if (to.includes("@")) {
      btn.href = `mailto:${to}?subject=${encodeURIComponent("Spark: " + title)}&body=${encodeURIComponent(msg)}`;
    } else if (to) {
      btn.href = `sms:${to}?&body=${encodeURIComponent(msg)}`;
    } else {
      btn.href = "#";
      btn.addEventListener("click", async e => {
        e.preventDefault();
        try {
          await navigator.clipboard.writeText(msg);
          said.textContent = `copied: "${msg}"`;
        } catch {
          said.textContent = `send: "${msg}"`;
        }
      });
    }
  });
}


// The spark animation plays once and stays on its final frame. Anyone who has
// asked their system to reduce motion gets the poster and nothing moving.
const anim = document.querySelector(".anim");
if (anim) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    anim.removeAttribute("autoplay");
    anim.pause();
  } else {
    // start from the top even if the browser restored a cached position
    anim.addEventListener("loadeddata", () => { anim.currentTime = 0; }, { once: true });
  }
}
