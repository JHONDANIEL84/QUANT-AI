import { HealthResponse, SystemStatusResponse } from "@/types/system";

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
