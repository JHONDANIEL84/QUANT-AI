"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Layers,
  LineChart,
  Cpu,
  Eye,
  Mic,
  Shield,
  FolderGit2,
  Sliders,
  Sparkles,
  BarChart3,
  Search,
  BookOpen,
} from "lucide-react";

export function Navbar() {
  const [currentTime, setCurrentTime] = useState<string>("");

  useEffect(() => {
    const updateBogotaTime = () => {
      const now = new Date();
      const formatted = new Intl.DateTimeFormat("es-CO", {
        timeZone: "America/Bogota",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }).format(now);
      setCurrentTime(formatted);
    };

    updateBogotaTime();
    const timer = setInterval(updateBogotaTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/90 backdrop-blur-md">
      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        {/* Brand & Market Status */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-quant-blue to-quant-cyan p-1 shadow-lg shadow-quant-blue/20">
              <Activity className="h-5 w-5 text-white animate-pulse" />
            </div>
            <div>
              <span className="font-mono text-base font-bold tracking-wider text-white">
                QUANT<span className="text-quant-cyan">.AI</span>
              </span>
              <span className="ml-2 rounded border border-quant-cyan/30 bg-quant-cyan/10 px-1.5 py-0.2 text-[10px] font-medium tracking-wide text-quant-cyan uppercase">
                v0.1.0 • FASE 1
              </span>
            </div>
          </div>

          <div className="hidden items-center space-x-2 border-l border-border pl-4 lg:flex text-xs text-gray-400">
            <span className="flex h-2 w-2 rounded-full bg-quant-green animate-ping" />
            <span className="text-gray-300 font-mono">BOGOTÁ (UTC-5):</span>
            <span className="font-mono font-medium text-white">{currentTime || "--:--:--"}</span>
            <span className="text-gray-500">•</span>
            <span className="rounded bg-surface-card px-1.5 py-0.5 font-mono text-[11px] text-quant-amber">
              COP / USD
            </span>
          </div>
        </div>

        {/* Quick Nav Badges */}
        <nav className="hidden md:flex items-center space-x-1 text-xs">
          <button className="flex items-center space-x-1.5 rounded-md bg-quant-cyan/10 px-3 py-1.5 text-quant-cyan font-medium border border-quant-cyan/30">
            <BarChart3 className="h-3.5 w-3.5" />
            <span>Dashboard</span>
          </button>
          <button className="flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-gray-400 hover:text-white hover:bg-surface-hover transition-colors">
            <LineChart className="h-3.5 w-3.5" />
            <span>Chart & SMC</span>
          </button>
          <button className="flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-gray-400 hover:text-white hover:bg-surface-hover transition-colors">
            <Layers className="h-3.5 w-3.5" />
            <span>Liquidity Intel</span>
          </button>
          <button className="flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-gray-400 hover:text-white hover:bg-surface-hover transition-colors">
            <Search className="h-3.5 w-3.5" />
            <span>Scanner</span>
          </button>
          <button className="flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-gray-400 hover:text-white hover:bg-surface-hover transition-colors">
            <Cpu className="h-3.5 w-3.5" />
            <span>Backtesting</span>
          </button>
          <button className="flex items-center space-x-1.5 rounded-md px-3 py-1.5 text-gray-400 hover:text-white hover:bg-surface-hover transition-colors">
            <BookOpen className="h-3.5 w-3.5" />
            <span>Journal</span>
          </button>
        </nav>

        {/* AI Capabilities Trigger Badges */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 rounded-full border border-border bg-surface-card px-2.5 py-1 text-xs">
            <Sparkles className="h-3.5 w-3.5 text-quant-purple" />
            <span className="hidden sm:inline font-mono text-[11px] text-gray-300">QUANT AI Chat</span>
          </div>

          <div className="flex items-center space-x-1 rounded-full border border-border bg-surface-card px-2.5 py-1 text-xs">
            <Eye className="h-3.5 w-3.5 text-quant-cyan" />
            <span className="hidden sm:inline font-mono text-[11px] text-gray-300">Live Vision</span>
          </div>

          <div className="flex items-center space-x-1 rounded-full border border-border bg-surface-card px-2.5 py-1 text-xs">
            <Mic className="h-3.5 w-3.5 text-quant-green" />
            <span className="hidden sm:inline font-mono text-[11px] text-gray-300">Voice Assistant</span>
          </div>
        </div>
      </div>
    </header>
  );
}
