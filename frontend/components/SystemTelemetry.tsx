"use client";

import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Server,
  Database,
  Cpu,
  Layers,
  Activity,
  Globe2,
  Lock,
  Clock,
} from "lucide-react";
import { fetchHealth, fetchSystemStatus } from "@/services/api";
import { HealthResponse, SystemStatusResponse, ServiceHealth } from "@/types/system";

export function SystemTelemetry() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastCheck, setLastCheck] = useState<Date>(new Date());

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [healthData, statusData] = await Promise.all([
        fetchHealth(),
        fetchSystemStatus(),
      ]);
      setHealth(healthData);
      setStatus(statusData);
      setLastCheck(new Date());
    } catch (err: any) {
      setError(err?.message || "No se pudo conectar con el backend de QUANT AI.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (serviceStatus: ServiceHealth["status"]) => {
    switch (serviceStatus) {
      case "healthy":
        return (
          <span className="flex items-center space-x-1 text-quant-green text-xs font-mono font-medium">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>OPERATIVO</span>
          </span>
        );
      case "degraded":
        return (
          <span className="flex items-center space-x-1 text-quant-amber text-xs font-mono font-medium">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>DEGRADADO</span>
          </span>
        );
      case "unconfigured":
        return (
          <span className="flex items-center space-x-1 text-gray-400 text-xs font-mono font-medium">
            <Lock className="h-3.5 w-3.5" />
            <span>PENDIENTE CONFIG</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 text-quant-red text-xs font-mono font-medium">
            <XCircle className="h-3.5 w-3.5" />
            <span>DESCONECTADO</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Backend Connection Status */}
      <div className="rounded-xl border border-border bg-surface p-5 shadow-2xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-lg border ${
                error
                  ? "border-quant-red/30 bg-quant-red/10 text-quant-red"
                  : "border-quant-green/30 bg-quant-green/10 text-quant-green"
              }`}
            >
              <Server className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-mono text-sm font-semibold tracking-wide text-white">
                  BACKEND FASTAPI QUANT ENGINE
                </h3>
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-mono font-medium ${
                    error
                      ? "bg-quant-red/20 text-quant-red border border-quant-red/40"
                      : "bg-quant-green/20 text-quant-green border border-quant-green/40"
                  }`}
                >
                  {error ? "DESCONECTADO" : "ONLINE / OPERATIVO"}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Host: <span className="font-mono text-gray-300">http://localhost:8000</span> • API:{" "}
                <span className="font-mono text-quant-cyan">/api/v1</span> • Moneda:{" "}
                <span className="font-mono text-quant-amber">COP</span> • Zona:{" "}
                <span className="font-mono text-white">America/Bogota</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto justify-between sm:justify-end">
            <div className="text-right text-xs text-gray-400">
              <div>Último ping:</div>
              <div className="font-mono text-gray-300">
                {lastCheck.toLocaleTimeString("es-CO")}
              </div>
            </div>
            <button
              onClick={loadData}
              disabled={isLoading}
              className="flex items-center space-x-1.5 rounded-lg border border-border-light bg-surface-card hover:bg-surface-hover px-3 py-2 text-xs font-medium text-white transition-all disabled:opacity-50"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 text-quant-cyan ${
                  isLoading ? "animate-spin" : ""
                }`}
              />
              <span>{isLoading ? "Verificando..." : "Actualizar"}</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-quant-red/30 bg-quant-red/10 p-3 text-xs text-quant-red flex items-center space-x-2">
            <XCircle className="h-4 w-4 shrink-0" />
            <span>
              Error de conexión con el backend: {error}. Asegúrate de que el servidor FastAPI esté iniciado en el puerto 8000.
            </span>
          </div>
        )}
      </div>

      {/* Grid of Microservices & Data Providers */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h4 className="font-mono text-xs font-semibold tracking-wider text-gray-400 uppercase">
            ESTADO DE MÓDULOS Y PROVEEDORES DE MERCADO
          </h4>
          <span className="text-[11px] font-mono text-gray-500">
            Fase 1 — Base de Infraestructura
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {status?.services.map((service, index) => (
            <div
              key={index}
              className="rounded-xl border border-border bg-surface p-4 hover:border-border-light transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-white tracking-wide">
                    {service.name.toUpperCase()}
                  </span>
                  {getStatusBadge(service.status)}
                </div>
                <p className="text-xs text-gray-400 leading-relaxed mb-3">
                  {service.details}
                </p>
              </div>

              <div className="flex items-center justify-between border-t border-border pt-2 text-[11px] font-mono text-gray-500">
                <span>Latencia:</span>
                <span className="text-gray-300">{service.latency_ms} ms</span>
              </div>
            </div>
          )) || (
            <div className="col-span-3 rounded-xl border border-border bg-surface p-8 text-center text-gray-500 text-xs font-mono">
              Cargando telemetría de módulos y adaptadores...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
