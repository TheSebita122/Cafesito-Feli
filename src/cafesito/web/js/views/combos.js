import { api } from "../api.js";
import { $, el, fillSelect, hideMessage, showMessage } from "../dom.js";
import { formatPercent } from "../format.js";

const USEFUL_LIFT = 1.2;
const STRONG_LIFT = 5;

let initialised = false;

function reading(rule) {
  if (rule.lift >= STRONG_LIFT) return { text: "Muy fuerte: ofrécelo siempre", tone: "strong" };
  if (rule.lift > USEFUL_LIFT) return { text: "Útil: ideal para un combo", tone: "useful" };
  return { text: "Coincidencia: no justifica un combo", tone: "weak" };
}

function ruleRow(rule) {
  const { text, tone } = reading(rule);
  return el("tr", {}, [
    el("td", { className: "product-name", text: rule.antecedent.join(", ") }),
    el("td", { className: "product-name", text: rule.consequent.join(", ") }),
    el("td", { className: "text-right font-mono-data", text: formatPercent(rule.support) }),
    el("td", { className: "text-right font-mono-data", text: formatPercent(rule.confidence) }),
    el("td", { className: "text-right font-mono-data accent-text", text: `${rule.lift.toFixed(2)}×` }),
    el("td", {}, el("span", { className: `reading reading-${tone}`, text })),
  ]);
}

async function loadRules() {
  const error = $("#combosError");
  hideMessage(error);
  try {
    const { rules } = await api.recommendations($("#comboProduct").value);
    $("#rulesBody").replaceChildren(...rules.map(ruleRow));
    $("#rulesEmpty").hidden = rules.length > 0;
  } catch (failure) {
    $("#rulesBody").replaceChildren();
    showMessage(error, failure.message);
  }
}

export async function showCombos() {
  if (initialised) return;
  try {
    const { product_types: types } = await api.productTypes();
    fillSelect($("#comboProduct"), [{ value: "", label: "Todas las reglas" }, ...types.map((type) => ({ value: type, label: type }))]);
    $("#comboProduct").addEventListener("change", loadRules);
    initialised = true;
  } catch (failure) {
    showMessage($("#combosError"), failure.message);
    return;
  }
  await loadRules();
}
