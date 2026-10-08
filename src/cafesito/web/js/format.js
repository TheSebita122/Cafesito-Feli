export const MONTH_NAMES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

export const MONTH_ABBREVIATIONS = [
  "Ene",
  "Feb",
  "Mar",
  "Abr",
  "May",
  "Jun",
  "Jul",
  "Ago",
  "Sep",
  "Oct",
  "Nov",
  "Dic",
];

export const WEEKDAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

export const SEGMENTS = {
  star: {
    name: "Estrella",
    color: "#6B3A2A",
    description: "Bebidas de alta rotación que sostienen el negocio. Prioriza su stock y evita quiebres.",
  },
  complement: {
    name: "Complemento",
    color: "#C17A45",
    description: "Pastelería y jarabes que acompañan la compra principal. Ideales para ofrecer en caja.",
  },
  premium_niche: {
    name: "Premium de nicho",
    color: "#4F7C82",
    description: "Precio alto y poca rotación. Revisa el surtido y promociónalos como regalo.",
  },
};

export function segmentInfo(key) {
  return SEGMENTS[key] ?? { name: key, color: "#7C6B60", description: "" };
}

const numberFormat = new Intl.NumberFormat("es-CL");
const currencyFormat = new Intl.NumberFormat("es-CL", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const currencyPreciseFormat = new Intl.NumberFormat("es-CL", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const percentFormat = new Intl.NumberFormat("es-CL", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export const formatNumber = (value) => numberFormat.format(value);
export const formatCurrency = (value) => currencyFormat.format(value);
export const formatCurrencyPrecise = (value) => currencyPreciseFormat.format(value);
export const formatPercent = (value) => percentFormat.format(value);

export function formatCompactCurrency(value) {
  if (Math.abs(value) >= 1000) {
    return `US$${(value / 1000).toLocaleString("es-CL", { maximumFractionDigits: 1 })} mil`;
  }
  return formatCurrencyPrecise(value);
}

export function formatAxisCurrency(value) {
  if (Math.abs(value) >= 1000) {
    return `$${(value / 1000).toLocaleString("es-CL", { maximumFractionDigits: 1 })}K`;
  }
  return `$${value}`;
}

export function formatCompactNumber(value) {
  if (Math.abs(value) >= 1000) {
    return `${(value / 1000).toLocaleString("es-CL", { maximumFractionDigits: 1 })} mil`;
  }
  return formatNumber(value);
}

export function formatHour(hour) {
  return `${String(hour).padStart(2, "0")}:00`;
}

export function formatSignedPercent(value) {
  const text = formatPercent(Math.abs(value));
  return `${value >= 0 ? "↑ +" : "↓ −"}${text}`;
}
