export interface ServiceHealth {
  name: string;
  status: "healthy" | "degraded" | "unreachable" | "unconfigured" | "disabled";
  latency_ms: number;
  details: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  app_name: string;
  timestamp: string;
  timezone: string;
  currency: string;
  environment: string;
}

export interface SystemStatusResponse {
  status: string;
  timestamp: string;
  timezone: string;
  default_currency: string;
  services: ServiceHealth[];
  capabilities: Record<string, boolean>;
  metadata: Record<string, any>;
}
