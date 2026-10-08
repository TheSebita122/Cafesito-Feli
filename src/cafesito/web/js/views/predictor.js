import { api } from "../api.js";
import { $, el, fillSelect, hideMessage, setBusy, showMessage } from "../dom.js";
import { MONTH_NAMES, WEEKDAY_NAMES, formatHour, formatPercent } from "../format.js";

let options = null;
let initialised = false;

function renderResult(prediction, request) {
  const high = prediction.level === "high";
  const container = $("#predictorResult");
  const probability = high ? prediction.probability_high : 1 - prediction.probability_high;
  container.className = `card result-card ${high ? "result-high" : "result-low"}`;
  container.replaceChildren(
    el("p", { className: "result-eyebrow", text: `${prediction.store_location} · ${WEEKDAY_NAMES[request.weekday]} · ${formatHour(request.hour)} · ${MONTH_NAMES[request.month - 1]}` }),
    el("h3", { className: "font-display result-title", text: high ? "Demanda alta" : "Demanda baja" }),
    el("p", { className: "result-confidence", text: `Confianza del modelo: ${formatPercent(probability)}` }),
    el("div", { className: "meter", attrs: { role: "img", "aria-label": `Probabilidad de demanda alta ${formatPercent(prediction.probability_high)}` } },
      el("span", { className: "meter-fill", attrs: { style: `width: ${(prediction.probability_high * 100).toFixed(1)}%` } }),
    ),
    el("p", { className: "result-advice", text: high
      ? `Se espera más de ${prediction.threshold} transacciones en esa hora. Refuerza el turno con más personal.`
      : `Se espera ${prediction.threshold} transacciones o menos en esa hora. Puedes operar con dotación reducida.` }),
    el("p", { className: "result-note", text: "Es una guía de apoyo: el modelo acierta en alrededor de 3 de cada 4 horas." }),
  );
}

async function loadOptions() {
  options = await api.demandOptions();
  fillSelect($("#predStore"), options.stores.map((store) => ({ value: store.id, label: store.location })));
  fillSelect($("#predWeekday"), WEEKDAY_NAMES.map((name, index) => ({ value: index, label: name })));
  fillSelect($("#predMonth"), options.months.map((month) => ({ value: month, label: MONTH_NAMES[month - 1] })));
  fillSelect($("#predHour"), options.hours.map((hour) => ({ value: hour, label: formatHour(hour) })), 8);
}

async function submit(event) {
  event.preventDefault();
  const error = $("#predictorError");
  const button = $("#predictBtn");
  hideMessage(error);
  const request = {
    store_id: Number($("#predStore").value),
    weekday: Number($("#predWeekday").value),
    month: Number($("#predMonth").value),
    hour: Number($("#predHour").value),
  };
  setBusy(button, true, "Calculando…");
  try {
    renderResult(await api.predictDemand(request), request);
  } catch (failure) {
    showMessage(error, failure.message);
  } finally {
    setBusy(button, false);
  }
}

export async function showPredictor() {
  if (initialised) return;
  const error = $("#predictorError");
  try {
    await loadOptions();
    $("#predictorForm").addEventListener("submit", submit);
    initialised = true;
  } catch (failure) {
    showMessage(error, failure.message);
  }
}
