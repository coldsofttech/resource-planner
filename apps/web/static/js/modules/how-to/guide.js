"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const links = document.querySelectorAll(".rp-docs-nav-link[href^='#']");
  const sections = [...links]
    .map((l) => document.querySelector(l.getAttribute("href")))
    .filter(Boolean);

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((l) => l.classList.remove("active"));
        const active = [...links].find((l) => l.getAttribute("href") === `#${entry.target.id}`);
        if (active) active.classList.add("active");
      });
    },
    { rootMargin: "-10% 0px -80% 0px" },
  );

  sections.forEach((s) => observer.observe(s));
});
