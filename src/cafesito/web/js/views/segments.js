import { api } from "../api.js";
import { $, el, fillSelect, hideMessage, setBusy, showMessage } from "../dom.js";
import {
  SEGMENTS,
  formatCurrency,
  formatCurrencyPrecise,
  formatNumber,
  formatPercent,
  segmentInfo,
} from "../format.js";

let products = [];
let initialised = false;

function profileCard(profile) {
  const info = segmentInfo(profile.segment);
  return el("article", { className: "card segment-card", attrs: { style: `border-top: 4px solid ${info.color}` } }, [
    el("h3", { className: "font-display", text: info.name }),
    el("p", { className: "card-sub", text: info.description }),
    el("dl", { className: "stat-list" }, [
      el("div", {}, [el("dt", { text: "Productos" }), el("dd", { text: formatNumber(profile.products) })]),
      el("div", {}, [el("dt", { text: "% de ingresos" }), el("dd", { text: formatPercent(profile.revenue_share) })]),
      el("div", {}, [el("dt", { text: "% de unidades" }), el("dd", { text: formatPercent(profile.units_share) })]),
      el("div", {}, [el("dt", { text: "Precio promedio" }), el("dd", { text: formatCurrencyPrecise(profile.avg_price) })]),
    ]),
  ]);
}

function renderProducts() {
  const filter = $("#segmentFilter").value;
  const rows = products
    .filter((product) => !filter || product.segment === filter)
    .sort((a, b) => b.revenue - a.revenue);
  $("#segmentProducts").replaceChildren(
    ...rows.map((product) => {
      const info = segmentInfo(product.segment);
      return el("tr", {}, [
        el("td", {}, [el("p", { className: "product-name", text: product.detail }), el("p", { className: "product-cat", text: product.category })]),
        el("td", {}, el("span", { className: "segment-tag", text: info.name, attrs: { style: `--tag-color: ${info.color}` } })),
        el("td", { className: "text-right font-mono-data", text: formatNumber(product.units) }),
        el("td", { className: "text-right font-mono-data accent-text", text: formatCurrency(product.revenue) }),
      ]);
    }),
  );
}

async function classify(event) {
  event.preventDefault();
  const error = $("#classifyError");
  const result = $("#classifyResult");
  hideMessage(error);
  result.replaceChildren();
  const body = {
    units: Number($("#classUnits").value),
    revenue: Number($("#classRevenue").value),
    avg_price: Number($("#classPrice").value),
  };
  if ([$("#classUnits"), $("#classRevenue"), $("#classPrice")].some((input) => input.value === "")) {
    showMessage(error, "Completa las tres cifras para clasificar el producto.");
    return;
  }
  const button = $("#classifyForm button[type=submit]");
  setBusy(button, true, "Clasificando…");
  try {
    const { segment } = await api.classifySegment(body);
    const info = segmentInfo(segment);
    result.replaceChildren(
      el("span", { className: "segment-tag", text: info.name, attrs: { style: `--tag-color: ${info.color}` } }),
      el("p", { className: "card-sub", text: info.description }),
    );
  } catch (failure) {
    showMessage(error, failure.message);
  } finally {
    setBusy(button, false);
  }
}

export async function showSegments() {
  if (initialised) return;
  const error = $("#segmentsError");
  try {
    const data = await api.segments();
    products = data.products;
    $("#segmentProfiles").replaceChildren(...data.profiles.map(profileCard));
    fillSelect($("#segmentFilter"), [
      { value: "", label: "Todos los segmentos" },
      ...Object.entries(SEGMENTS).map(([value, info]) => ({ value, label: info.name })),
    ]);
    $("#segmentFilter").addEventListener("change", renderProducts);
    $("#classifyForm").addEventListener("submit", classify);
    renderProducts();
    hideMessage(error);
    initialised = true;
  } catch (failure) {
    showMessage(error, failure.message);
  }
}
