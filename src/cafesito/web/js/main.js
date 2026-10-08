import { $ } from "./dom.js";
import { initDashboard, showDashboard } from "./views/dashboard.js";
import { showCombos } from "./views/combos.js";
import { showPredictor } from "./views/predictor.js";
import { showSegments } from "./views/segments.js";

const VIEWS = {
  dashboard: showDashboard,
  predictor: showPredictor,
  segments: showSegments,
  combos: showCombos,
};
const DEFAULT_VIEW = "dashboard";

function currentView() {
  const name = window.location.hash.replace("#", "");
  return name in VIEWS ? name : DEFAULT_VIEW;
}

async function navigate() {
  const active = currentView();
  document.querySelectorAll(".view").forEach((section) => {
    section.hidden = section.id !== `view-${active}`;
  });
  document.querySelectorAll(".main-nav a").forEach((link) => {
    const isActive = link.dataset.view === active;
    link.classList.toggle("active", isActive);
    if (isActive) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  $("#dashboardFilters").hidden = active !== "dashboard";
  await VIEWS[active]();
}

window.addEventListener("hashchange", navigate);

initDashboard().then(navigate);
