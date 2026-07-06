"use strict";

// Map old single-page anchor IDs to the new per-module URLs.
const ANCHOR_REDIRECT_MAP = {
  overview: "/docs/guide/",
  concepts: "/docs/guide/",
  "financial-years": "/docs/guide/financial-years/",
  sprints: "/docs/guide/sprints/",
  "sprint-forecast": "/docs/guide/sprint-forecast/",
  "sprint-actuals": "/docs/guide/sprint-actuals/",
  projects: "/docs/guide/projects/",
  estimates: "/docs/guide/estimates/",
  "project-sizes": "/docs/guide/project-sizes/",
  "project-links": "/docs/guide/project-links/",
  "project-attachments": "/docs/guide/project-attachments/",
  "project-budgets": "/docs/guide/project-budgets/",
  "project-actuals": "/docs/guide/project-actuals/",
  "project-contacts": "/docs/guide/project-contacts/",
  "project-comments": "/docs/guide/project-comments/",
  programmes: "/docs/guide/programmes/",
  teams: "/docs/guide/teams/",
  members: "/docs/guide/members/",
  leaves: "/docs/guide/leaves/",
  "business-units": "/docs/guide/business-units/",
  roles: "/docs/guide/roles/",
  skills: "/docs/guide/skills/",
  "employment-types": "/docs/guide/employment-types/",
  locations: "/docs/guide/locations/",
  holidays: "/docs/guide/holidays/",
  tags: "/docs/guide/tags/",
  "recharge-types": "/docs/guide/recharge-types/",
};

document.addEventListener("DOMContentLoaded", () => {
  // Redirect old anchor-based bookmarks (e.g. /docs/guide/#sprints) to
  // the new per-page URL.
  const hash = window.location.hash.slice(1);
  if (hash && ANCHOR_REDIRECT_MAP[hash]) {
    window.location.replace(ANCHOR_REDIRECT_MAP[hash]);
    return;
  }

  // Highlight the sidebar link that matches the current path.
  const currentPath = window.location.pathname;
  document.querySelectorAll(".rp-docs-nav-link").forEach((link) => {
    const href = link.getAttribute("href");
    if (href && currentPath === href) {
      link.classList.add("active");
    }
  });
});
