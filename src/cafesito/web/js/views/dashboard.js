import { api } from "../api.js";
import {
  renderCategoryChart,
  renderHourlyChart,
  renderMonthlyChart,
  renderSegmentScatter,
} from "../charts.js";
import { $, el, fillSelect, hideMessage, showMessage } from "../dom.js";
import {
  MONTH_ABBREVIATIONS,
  formatCompactCurrency,
  formatCompactNumber,
  formatCurrency,
  formatCurrencyPrecise,
  formatNumber,
  formatSignedPercent,
  segmentInfo,
} from "../format.js";

const KPI_FIELDS = [
  { key: "revenue", value: "kpiRevenue", trend: "trendRevenue", sub: "subRevenue", format: formatCompactCurrency },
  { key: "transactions", value: "kpiTransactions", trend: "trendTransactions", sub: "subTransactions", format: formatCompactNumber },
  { key: "units", value: "kpiUnits", trend: "trendUnits", sub: "subUnits", format: formatCompactNumber },
  { key: "average_ticket", value: "kpiTicket", trend: "trendTicket", sub: "subTicket", format: formatCurrencyPrecise },
];

const DEFAULT_SUBTITLES = {
  revenue: "en el período",
  transactions: "líneas de venta",
  units: "unidades",
  average_ticket: "por transacción",
};

let segmentsLoaded = false;

function currentFilters() {
  return {
    store_id: $("#storeSelect").value,
    quarter: $("#quarterSelect").value,
  };
}

function renderKpis(kpis) {
  hideMessage($("#kpiError"));
  KPI_FIELDS.forEach(({ key, value, trend, sub, format }) => {
    $(`#${value}`).textContent = format(kpis[key]);
    const badge = $(`#${trend}`);
    const change = kpis.variation?.[key];
    if (change === null || change === undefined) {
      badge.hidden = true;
      $(`#${sub}`).textContent = DEFAULT_SUBTITLES[key];
      return;
    }
    badge.hidden = false;
    badge.textContent = formatSignedPercent(change);
    badge.className = `trend-badge ${change >= 0 ? "positive" : "negative"}`;
    $(`#${sub}`).textContent = "vs trimestre anterior";
  });
}

function renderKpiFailure(error) {
  KPI_FIELDS.forEach(({ value, trend }) => {
    $(`#${value}`).textContent = "—";
    $(`#${trend}`).hidden = true;
  });
  showMessage($("#kpiError"), error.message);
}

function renderTopProducts(products) {
  const body = $("#topProductsBody");
  body.replaceChildren(
    ...products.map((product, index) => {
      const first = index === 0;
      return el("tr", { className: first ? "highlight-row" : "" }, [
        el("td", { className: "td-num" }, el("span", { className: `font-mono-data ${first ? "primary-text" : "muted-text"}`, text: String(index + 1).padStart(2, "0") })),
        el("td", {}, [
          el("p", { className: `product-name ${first ? "primary-text" : ""}`, text: product.name }),
          el("p", { className: "product-cat", text: product.category }),
        ]),
        el("td", { className: "text-right font-mono-data", text: formatNumber(product.units) }),
        el("td", { className: "text-right font-mono-data accent-text", text: formatCurrency(product.revenue) }),
      ]);
    }),
  );
}

async function guarded(errorId, task) {
  const container = $(`#${errorId}`);
  try {
    hideMessage(container);
    await task();
  } catch (error) {
    showMessage(container, error.message);
  }
}

async function loadFilteredSections() {
  const filters = currentFilters();
  await Promise.all([
    (async () => {
      try {
        renderKpis(await api.kpis(filters));
      } catch (error) {
        renderKpiFailure(error);
      }
    })(),
    guarded("categoryError", async () => renderCategoryChart(await api.salesByCategory(filters))),
    guarded("monthlyError", async () => renderMonthlyChart(await api.salesMonthly(filters), MONTH_ABBREVIATIONS)),
    guarded("hourlyError", async () => renderHourlyChart(await api.salesHourly(filters))),
    guarded("topProductsError", async () => renderTopProducts(await api.topProducts(filters))),
  ]);
}

async function loadSegmentScatter() {
  if (segmentsLoaded) return;
  await guarded("segmentScatterError", async () => {
    const { products } = await api.segments();
    renderSegmentScatter("segmentScatter", products, segmentInfo);
    segmentsLoaded = true;
  });
}

export async function initDashboard() {
  try {
    const stores = await api.stores();
    fillSelect($("#storeSelect"), [{ value: "", label: "Todas las sedes" }, ...stores.map((store) => ({ value: store.id, label: store.location }))]);
  } catch (error) {
    showMessage($("#kpiError"), error.message);
  }
  $("#storeSelect").addEventListener("change", loadFilteredSections);
  $("#quarterSelect").addEventListener("change", loadFilteredSections);
}

export async function showDashboard() {
  await Promise.all([loadFilteredSections(), loadSegmentScatter()]);
}
