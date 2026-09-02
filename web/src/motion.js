/* Motion, added as progressive enhancement.

   The rule this file follows: nothing is hidden until JavaScript has
   confirmed motion is welcome. A reveal built the usual way -- opacity 0 in
   the stylesheet, JS class to bring it back -- leaves a blank page for
   anyone whose script never runs, and that failure mode is far worse than
   having no animation. So the hiding is applied by JS, in JS's absence the
   page simply renders finished.

   Everything here also yields to prefers-reduced-motion. Vestibular
   disorders make scroll-triggered movement genuinely unpleasant, and the
   setting is the reader telling us so.
*/

import { useEffect, useState } from "react";

export function prefersReducedMotion() {
  return typeof window !== "undefined"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/* Fade-and-rise as each marked element reaches the viewport.

   `key` re-runs the effect when the view changes, because switching from
   landing to results mounts entirely new nodes that the old observer has
   never seen. */
export function useReveal(key) {
  useEffect(() => {
    if (prefersReducedMotion()) return undefined;

    document.documentElement.classList.add("motion-on");

    const targets = document.querySelectorAll("[data-reveal]:not(.is-in)");
    if (!targets.length) return undefined;

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);   // one-way: no re-animation on scroll up
        }
      },
      // Fires slightly before the element is fully in view, so the movement
      // has finished by the time it is being read.
      { threshold: 0.05, rootMargin: "0px 0px -8% 0px" },
    );

    targets.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [key]);
}

/* Counts 0 -> target once, driven by rAF rather than a CSS transition.

   The same animated number drives both the label and the dial's --pct, so
   the sweep and the digits cannot drift apart -- which they do if one is a
   CSS transition and the other a JS timer. */
export function useCountUp(target, ms = 900) {
  const [value, setValue] = useState(() => (prefersReducedMotion() ? target : 0));

  useEffect(() => {
    if (prefersReducedMotion()) {
      setValue(target);
      return undefined;
    }

    let raf = 0;
    let start = null;
    const easeOutCubic = (t) => 1 - (1 - t) ** 3;

    const tick = (now) => {
      if (start === null) start = now;
      const p = Math.min(1, (now - start) / ms);
      setValue(Math.round(target * easeOutCubic(p)));
      if (p < 1) raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);

  return value;
}

/* True after the first paint. Lets a bar render at zero width and then get
   its real width, so the CSS transition has something to animate from.
   Setting the final width on the first render would just paint it there. */
export function useMounted(delay = 60) {
  const [mounted, setMounted] = useState(() => prefersReducedMotion());

  useEffect(() => {
    if (prefersReducedMotion()) return undefined;
    const t = setTimeout(() => setMounted(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  return mounted;
}

/* Depth on pointer move: writes --rx / --ry onto the element for a CSS
   transform to pick up.

   Kept deliberately shallow. The point is that the panel has a surface and
   sits in space -- not that it swings around. Anything past a few degrees
   stops reading as depth and starts reading as a gimmick.

   Pointer-only and reduced-motion-aware: a touch device has no hover to
   drive it, and a tilting panel is exactly the kind of movement the reduced
   -motion setting is asking us not to make. */
export function useTilt(ref, max = 5) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    if (prefersReducedMotion()) return undefined;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return undefined;

    let raf = 0;

    const onMove = (e) => {
      const r = el.getBoundingClientRect();
      // -0.5 .. 0.5 from the centre of the element.
      const dx = (e.clientX - r.left) / r.width - 0.5;
      const dy = (e.clientY - r.top) / r.height - 0.5;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        el.style.setProperty("--ry", `${(dx * max * 2).toFixed(2)}deg`);
        el.style.setProperty("--rx", `${(-dy * max * 2).toFixed(2)}deg`);
      });
    };

    const onLeave = () => {
      cancelAnimationFrame(raf);
      el.style.setProperty("--rx", "0deg");
      el.style.setProperty("--ry", "0deg");
    };

    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerleave", onLeave);
    return () => {
      cancelAnimationFrame(raf);
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerleave", onLeave);
    };
  }, [ref, max]);
}
