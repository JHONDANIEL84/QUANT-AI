import { HealthResponse, SystemStatusResponse } from "@/types/system";
import {
  MarketBar,
  TickerSnapshot,
  OrderBookDepth,
  MacroIndicator,
  ProviderHealth,
} from "@/types/market";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Error ${res.status}: Fallo al conectar con health endpoint`);
  }
  return res.json();
}

export async function fetchSystemStatus(): Promise<SystemStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/system/status`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Error ${res.status}: Fallo al conectar con status endpoint`);
  }
  return res.json();
}

export async function fetchMarketBars(
  symbol: string,
  interval: string = "1d",
  limit: number = 30
): Promise<MarketBar[]> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/market/bars?symbol=${encodeURIComponent(
      symbol
    )}&interval=${encodeURIComponent(interval)}&limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`Error ${res.status}: No se pudieron cargar las velas para ${symbol}`);
  }
  return res.json();
}

export async function fetchTicker(symbol: string): Promise<TickerSnapshot> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/market/ticker?symbol=${encodeURIComponent(symbol)}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`Error ${res.status}: No se pudo cargar el precio para ${symbol}`);
  }
  return res.json();
}

export async function fetchOrderBook(
  symbol: string = "BTCUSDT",
  limit: number = 10
): Promise<OrderBookDepth> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/market/orderbook?symbol=${encodeURIComponent(
      symbol
    )}&limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`Error ${res.status}: Libro de órdenes no disponible para ${symbol}`);
  }
  return res.json();
}

export async function fetchMacroIndicators(country: string = "CO"): Promise<MacroIndicator[]> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/market/macro?country=${encodeURIComponent(country)}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`Error ${res.status}: No se pudieron cargar indicadores macroeconómicos`);
  }
  return res.json();
}

export async function fetchProvidersStatus(): Promise<ProviderHealth[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/market/providers`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Error ${res.status}: Error al consultar estado de proveedores`);
  }
  return res.json();
}
