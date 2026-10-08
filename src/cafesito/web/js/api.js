const BASE = "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const NETWORK_MESSAGE = "No pudimos conectar con el servidor. Revisa tu conexión e inténtalo otra vez.";
const GENERIC_MESSAGE = "Algo salió mal. Inténtalo de nuevo en unos minutos.";

function buildQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

async function request(path, { method = "GET", params, body } = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}${buildQuery(params)}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(NETWORK_MESSAGE, 0);
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new ApiError(payload?.error?.message ?? GENERIC_MESSAGE, response.status);
  }
  return payload;
}

export const api = {
  stores: () => request("/stores"),
  kpis: (filters) => request("/kpis", { params: filters }),
  salesByCategory: (filters) => request("/sales/by-category", { params: filters }),
  salesMonthly: (filters) => request("/sales/monthly", { params: filters }),
  salesHourly: (filters) => request("/sales/hourly", { params: filters }),
  topProducts: (filters) => request("/products/top", { params: { ...filters, limit: 5 } }),
  demandOptions: () => request("/predictions/demand/options"),
  predictDemand: (body) => request("/predictions/demand", { method: "POST", body }),
  segments: () => request("/segments"),
  classifySegment: (body) => request("/segments/classify", { method: "POST", body }),
  productTypes: () => request("/product-types"),
  recommendations: (productType) =>
    request("/recommendations", { params: { product_type: productType } }),
};
