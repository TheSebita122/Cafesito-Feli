import { formatAxisCurrency, formatCompactNumber, formatCurrency, formatHour, formatNumber } from "./format.js";

const registry = new Map();

const FONT_MONO = "DM Mono";
const FONT_SANS = "Inter";
const GRID = { color: "#E4DDD6", borderDash: [3, 3] };
const MUTED = "#7C6B60";
const HEAT_COLORS = ["#EDD5B8", "#D9A87A", "#C17A45", "#8B5040", "#6B3A2A"];
const CATEGORY_COLORS = ["#6B3A2A", "#8B5040", "#C17A45", "#D9A87A"];

function mount(canvasId, config) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined") return;
  registry.get(canvasId)?.destroy();
  registry.set(canvasId, new Chart(canvas.getContext("2d"), config));
}

function baseOptions(extra = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, ...extra.plugins },
    scales: extra.scales,
    indexAxis: extra.indexAxis,
  };
}

function axisTitle(text) {
  return { display: true, text, color: MUTED, font: { family: FONT_SANS, size: 11 } };
}

export function renderCategoryChart(rows) {
  mount("categoryChart", {
    type: "bar",
    data: {
      labels: rows.map((row) => row.category),
      datasets: [
        {
          label: "Ingresos",
          data: rows.map((row) => row.revenue),
          backgroundColor: rows.map((_, index) => CATEGORY_COLORS[Math.min(index, CATEGORY_COLORS.length - 1)]),
          borderRadius: 4,
          barThickness: 16,
        },
      ],
    },
    options: baseOptions({
      indexAxis: "y",
      plugins: { tooltip: { callbacks: { label: (item) => formatCurrency(item.parsed.x) } } },
      scales: {
        x: {
          title: axisTitle("Ingresos (US$)"),
          grid: GRID,
          ticks: { font: { family: FONT_MONO, size: 11 }, color: MUTED, callback: (value) => formatAxisCurrency(value) },
        },
        y: { grid: { display: false }, ticks: { font: { family: FONT_SANS, size: 12 }, color: "#4A2C1E" } },
      },
    }),
  });
}

export function renderMonthlyChart(rows, monthLabels) {
  mount("monthlyChart", {
    type: "line",
    data: {
      labels: rows.map((row) => monthLabels[row.month - 1]),
      datasets: [
        {
          label: "Ingresos",
          data: rows.map((row) => row.revenue),
          borderColor: "#6B3A2A",
          backgroundColor: "#C17A45",
          borderWidth: 2.5,
          pointRadius: 5,
          pointBackgroundColor: "#C17A45",
          pointBorderColor: "#6B3A2A",
          pointBorderWidth: 2,
          tension: 0.2,
        },
      ],
    },
    options: baseOptions({
      plugins: { tooltip: { callbacks: { label: (item) => formatCurrency(item.parsed.y) } } },
      scales: {
        x: { title: axisTitle("Mes"), grid: GRID, ticks: { font: { family: FONT_SANS, size: 12 }, color: MUTED } },
        y: {
          title: axisTitle("Ingresos (US$)"),
          grid: GRID,
          ticks: { font: { family: FONT_MONO, size: 11 }, color: MUTED, callback: (value) => formatAxisCurrency(value) },
        },
      },
    }),
  });
}

export function renderHourlyChart(rows) {
  const peak = Math.max(...rows.map((row) => row.transactions), 1);
  const colorFor = (value) => {
    const ratio = value / peak;
    if (ratio > 0.85) return HEAT_COLORS[4];
    if (ratio > 0.65) return HEAT_COLORS[3];
    if (ratio > 0.45) return HEAT_COLORS[2];
    if (ratio > 0.25) return HEAT_COLORS[1];
    return HEAT_COLORS[0];
  };
  mount("hourlyChart", {
    type: "bar",
    data: {
      labels: rows.map((row) => formatHour(row.hour)),
      datasets: [
        {
          label: "Transacciones",
          data: rows.map((row) => row.transactions),
          backgroundColor: rows.map((row) => colorFor(row.transactions)),
          borderRadius: 3,
        },
      ],
    },
    options: baseOptions({
      plugins: { tooltip: { callbacks: { label: (item) => `${formatNumber(item.parsed.y)} transacciones` } } },
      scales: {
        x: { title: axisTitle("Hora del día"), grid: { display: false }, ticks: { font: { family: FONT_MONO, size: 10 }, color: MUTED } },
        y: { title: axisTitle("Transacciones"), grid: GRID, ticks: { font: { family: FONT_MONO, size: 10 }, color: MUTED, callback: (value) => formatCompactNumber(value) } },
      },
    }),
  });
}

export function renderSegmentScatter(canvasId, products, segmentInfo) {
  const keys = [...new Set(products.map((product) => product.segment))];
  mount(canvasId, {
    type: "scatter",
    data: {
      datasets: keys.map((key) => {
        const info = segmentInfo(key);
        return {
          label: info.name,
          data: products
            .filter((product) => product.segment === key)
            .map((product) => ({ x: product.units, y: product.revenue, name: product.detail })),
          backgroundColor: info.color,
          pointRadius: 5,
          pointHoverRadius: 7,
        };
      }),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { font: { family: FONT_SANS, size: 12 }, color: MUTED, usePointStyle: true } },
        tooltip: {
          callbacks: {
            label: (item) =>
              `${item.raw.name}: ${formatNumber(item.parsed.x)} unidades, ${formatCurrency(item.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { title: axisTitle("Unidades vendidas"), grid: GRID, ticks: { font: { family: FONT_MONO, size: 10 }, color: MUTED, callback: (value) => formatCompactNumber(value) } },
        y: { title: axisTitle("Ingresos (US$)"), grid: GRID, ticks: { font: { family: FONT_MONO, size: 10 }, color: MUTED, callback: (value) => formatAxisCurrency(value) } },
      },
    },
  });
}
