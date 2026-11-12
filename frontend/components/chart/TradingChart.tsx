"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  LineData,
  HistogramData,
  ColorType,
  Time,
} from "lightweight-charts";
import {
  LineChart,
  Layers,
  Activity,
  Sliders,
  Maximize2,
  RefreshCw,
  Eye,
  EyeOff,
  TrendingUp,
} from "lucide-react";
import { fetchChartData } from "@/services/api";
import { ChartDataResponse, FibonacciLevels } from "@/types/market";

const SYMBOLS = [
  { symbol: "BTCUSDT", label: "BTC/USDT", market: "Crypto" },
  { symbol: "ETHUSDT", label: "ETH/USDT", market: "Crypto" },
  { symbol: "AAPL", label: "Apple", market: "US Stock" },
  { symbol: "NVDA", label: "NVIDIA", market: "US Stock" },
  { symbol: "SPY", label: "S&P 500 ETF", market: "ETF" },
  { symbol: "ECOPETROL", label: "Ecopetrol", market: "BVC (COP)" },
  { symbol: "PFBCOLO", label: "Bancolombia", market: "BVC (COP)" },
];

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"];

export function TradingChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const oscillatorContainerRef = useRef<HTMLDivElement>(null);

  const [symbol, setSymbol] = useState<string>("BTCUSDT");
  const [interval, setInterval] = useState<string>("1d");
  const [data, setData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Indicator Toggle States
  const [showEMA20, setShowEMA20] = useState<boolean>(true);
  const [showEMA50, setShowEMA50] = useState<boolean>(false);
  const [showEMA200, setShowEMA200] = useState<boolean>(true);
  const [showVWAP, setShowVWAP] = useState<boolean>(false);
  const [showBollinger, setShowBollinger] = useState<boolean>(false);
  const [showFibonacci, setShowFibonacci] = useState<boolean>(false);
  const [activeOscillator, setActiveOscillator] = useState<"rsi" | "macd" | "none">("rsi");

  // Load chart data from API
  const loadData = async (sym: string, intv: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchChartData(sym, intv, 150);
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Error al cargar datos del gráfico.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData(symbol, interval);
  }, [symbol, interval]);

  // Render Lightweight Charts Main Canvas
  useEffect(() => {
    if (!chartContainerRef.current || !data || data.bars.length === 0) return;

    // Clean container
    chartContainerRef.current.innerHTML = "";

    const chart: IChartApi = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#080B11" },
        textColor: "#94A3B8",
      },
      grid: {
        vertLines: { color: "#131926" },
        horzLines: { color: "#131926" },
      },
      crosshair: {
        vertLine: { color: "#00E5FF", width: 1, style: 2 },
        horzLine: { color: "#00E5FF", width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: "#1F293D",
        textColor: "#94A3B8",
      },
      timeScale: {
        borderColor: "#1F293D",
        timeVisible: true,
        secondsVisible: false,
      },
      width: chartContainerRef.current.clientWidth,
      height: 480,
    });

    // 1. Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#00E676",
      downColor: "#FF5252",
      borderUpColor: "#00E676",
      borderDownColor: "#FF5252",
      wickUpColor: "#00E676",
      wickDownColor: "#FF5252",
    });

    const formattedCandles: CandlestickData<Time>[] = data.bars.map((b) => {
      const timeVal = (new Date(b.timestamp).getTime() / 1000) as Time;
      return {
        time: timeVal,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      };
    });

    // Sort by timestamp
    formattedCandles.sort((a, b) => (Number(a.time) - Number(b.time)));
    candleSeries.setData(formattedCandles);

    // 2. Volume Series (Overlay at bottom)
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "", // overlay scale
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });

    const formattedVolume: HistogramData<Time>[] = data.bars.map((b) => ({
      time: (new Date(b.timestamp).getTime() / 1000) as Time,
      value: b.volume,
      color: b.close >= b.open ? "#00E67622" : "#FF525222",
    }));
    formattedVolume.sort((a, b) => (Number(a.time) - Number(b.time)));
    volumeSeries.setData(formattedVolume);

    // 3. EMA 20 (Cyan)
    if (showEMA20 && data.indicators.ema_20) {
      const ema20Series = chart.addLineSeries({
        color: "#00E5FF",
        lineWidth: 2,
        title: "EMA 20",
      });
      const emaData: LineData<Time>[] = [];
      data.bars.forEach((b, i) => {
        const val = data.indicators.ema_20?.[i];
        if (val !== null && val !== undefined) {
          emaData.push({ time: (new Date(b.timestamp).getTime() / 1000) as Time, value: val });
        }
      });
      emaData.sort((a, b) => Number(a.time) - Number(b.time));
      ema20Series.setData(emaData);
    }

    // 4. EMA 50 (Yellow)
    if (showEMA50 && data.indicators.ema_50) {
      const ema50Series = chart.addLineSeries({
        color: "#FFD600",
        lineWidth: 2,
        title: "EMA 50",
      });
      const emaData: LineData<Time>[] = [];
      data.bars.forEach((b, i) => {
        const val = data.indicators.ema_50?.[i];
        if (val !== null && val !== undefined) {
          emaData.push({ time: (new Date(b.timestamp).getTime() / 1000) as Time, value: val });
        }
      });
      emaData.sort((a, b) => Number(a.time) - Number(b.time));
      ema50Series.setData(emaData);
    }

    // 5. EMA 200 (Purple)
    if (showEMA200 && data.indicators.ema_200) {
      const ema200Series = chart.addLineSeries({
        color: "#7C4DFF",
        lineWidth: 2,
        title: "EMA 200",
      });
      const emaData: LineData<Time>[] = [];
      data.bars.forEach((b, i) => {
        const val = data.indicators.ema_200?.[i];
        if (val !== null && val !== undefined) {
          emaData.push({ time: (new Date(b.timestamp).getTime() / 1000) as Time, value: val });
        }
      });
      emaData.sort((a, b) => Number(a.time) - Number(b.time));
      ema200Series.setData(emaData);
    }

    // 6. VWAP (Blue)
    if (showVWAP && data.indicators.vwap) {
      const vwapSeries = chart.addLineSeries({
        color: "#2979FF",
        lineWidth: 2,
        title: "VWAP",
      });
      const vwapData: LineData<Time>[] = [];
      data.bars.forEach((b, i) => {
        const val = data.indicators.vwap?.[i];
        if (val !== null && val !== undefined) {
          vwapData.push({ time: (new Date(b.timestamp).getTime() / 1000) as Time, value: val });
        }
      });
      vwapData.sort((a, b) => Number(a.time) - Number(b.time));
      vwapSeries.setData(vwapData);
    }

    // 7. Bollinger Bands
    if (showBollinger && data.indicators.bollinger_bands) {
      const upperSeries = chart.addLineSeries({ color: "#00E5FF88", lineWidth: 1, title: "BB Upper" });
      const midSeries = chart.addLineSeries({ color: "#90A4AE88", lineWidth: 1, title: "BB Middle" });
      const lowerSeries = chart.addLineSeries({ color: "#00E5FF88", lineWidth: 1, title: "BB Lower" });

      const uData: LineData<Time>[] = [];
      const mData: LineData<Time>[] = [];
      const lData: LineData<Time>[] = [];

      data.bars.forEach((b, i) => {
        const pt = data.indicators.bollinger_bands?.[i];
        if (pt) {
          const t = (new Date(b.timestamp).getTime() / 1000) as Time;
          uData.push({ time: t, value: pt.upper });
          mData.push({ time: t, value: pt.middle });
          lData.push({ time: t, value: pt.lower });
        }
      });
      upperSeries.setData(uData);
      midSeries.setData(mData);
      lowerSeries.setData(lData);
    }

    // 8. Fibonacci Retracements
    if (showFibonacci && data.indicators.fibonacci) {
      const fib = data.indicators.fibonacci;
      const ratios = ["0.0", "0.236", "0.382", "0.5", "0.618", "0.786", "1.0"];
      ratios.forEach((r) => {
        const p = fib.levels[r];
        if (p) {
          candleSeries.createPriceLine({
            price: p,
            color: r === "0.618" ? "#FFD600" : (r === "0.5" ? "#00E5FF" : "#64748B"),
            lineWidth: r === "0.618" || r === "0.5" ? 2 : 1,
            lineStyle: 2,
            axisLabelVisible: true,
            title: `Fib ${r} (${p.toFixed(2)})`,
          });
        }
      });
    }

    // Handle Resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data, showEMA20, showEMA50, showEMA200, showVWAP, showBollinger, showFibonacci]);

  // Render Oscillator Sub-panel (RSI or MACD)
  useEffect(() => {
    if (!oscillatorContainerRef.current || !data || activeOscillator === "none") return;
    oscillatorContainerRef.current.innerHTML = "";

    const oscChart = createChart(oscillatorContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#080B11" },
        textColor: "#94A3B8",
      },
      grid: {
        vertLines: { color: "#131926" },
        horzLines: { color: "#131926" },
      },
      rightPriceScale: {
        borderColor: "#1F293D",
      },
      timeScale: {
        borderColor: "#1F293D",
        timeVisible: true,
      },
      width: oscillatorContainerRef.current.clientWidth,
      height: 160,
    });

    if (activeOscillator === "rsi" && data.indicators.rsi_14) {
      const rsiSeries = oscChart.addLineSeries({
        color: "#00E5FF",
        lineWidth: 2,
        title: "RSI (14)",
      });
      const rsiData: LineData<Time>[] = [];
      data.bars.forEach((b, i) => {
        const val = data.indicators.rsi_14?.[i];
        if (val !== null && val !== undefined) {
          rsiData.push({ time: (new Date(b.timestamp).getTime() / 1000) as Time, value: val });
        }
      });
      rsiData.sort((a, b) => Number(a.time) - Number(b.time));
      rsiSeries.setData(rsiData);

      // Overbought 70 and Oversold 30 lines
      rsiSeries.createPriceLine({ price: 70, color: "#FF525288", lineWidth: 1, lineStyle: 2, title: "70 OB" });
      rsiSeries.createPriceLine({ price: 30, color: "#00E67688", lineWidth: 1, lineStyle: 2, title: "30 OS" });
      rsiSeries.createPriceLine({ price: 50, color: "#64748B44", lineWidth: 1, lineStyle: 2, title: "50" });
    } else if (activeOscillator === "macd" && data.indicators.macd) {
      const macdSeries = oscChart.addLineSeries({ color: "#2979FF", lineWidth: 2, title: "MACD" });
      const signalSeries = oscChart.addLineSeries({ color: "#FF9100", lineWidth: 2, title: "Signal" });
      const histSeries = oscChart.addHistogramSeries({ title: "Hist" });

      const mData: LineData<Time>[] = [];
      const sData: LineData<Time>[] = [];
      const hData: HistogramData<Time>[] = [];

      data.bars.forEach((b, i) => {
        const pt = data.indicators.macd?.[i];
        if (pt) {
          const t = (new Date(b.timestamp).getTime() / 1000) as Time;
          mData.push({ time: t, value: pt.macd });
          sData.push({ time: t, value: pt.signal });
          hData.push({
            time: t,
            value: pt.histogram,
            color: pt.histogram >= 0 ? "#00E676" : "#FF5252",
          });
        }
      });
      macdSeries.setData(mData);
      signalSeries.setData(sData);
      histSeries.setData(hData);
    }

    const handleResize = () => {
      if (oscillatorContainerRef.current) {
        oscChart.applyOptions({ width: oscillatorContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      oscChart.remove();
    };
  }, [data, activeOscillator]);

  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-2xl space-y-4">
      {/* Header Toolbar: Symbol Selector, Timeframes, and Indicators Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-3 border-b border-border">
        {/* Symbol & Market Selector */}
        <div className="flex flex-wrap items-center gap-2">
          {SYMBOLS.map((s) => (
            <button
              key={s.symbol}
              onClick={() => setSymbol(s.symbol)}
              className={`rounded-lg border px-3 py-1.5 font-mono text-xs font-semibold transition-all ${
                symbol === s.symbol
                  ? "border-quant-cyan bg-quant-cyan/15 text-white shadow-md shadow-quant-cyan/20"
                  : "border-border bg-surface-card text-gray-400 hover:text-white hover:border-border-light"
              }`}
            >
              <span>{s.label}</span>
              <span className="ml-1 text-[9px] text-gray-500 font-normal">({s.market})</span>
            </button>
          ))}
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center space-x-1 border border-border rounded-lg bg-surface-card p-1 self-start lg:self-auto font-mono text-xs">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => setInterval(tf)}
              className={`rounded px-2.5 py-1 transition-all ${
                interval === tf
                  ? "bg-quant-blue text-white font-bold"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Overlay Indicators Toggle Pills */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-gray-500 text-[11px] font-semibold uppercase mr-1">
            SUPERPOSICIONES:
          </span>

          <button
            onClick={() => setShowEMA20(!showEMA20)}
            className={`flex items-center space-x-1.5 rounded-md border px-2.5 py-1 transition-all ${
              showEMA20
                ? "border-quant-cyan/50 bg-quant-cyan/10 text-quant-cyan font-bold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-quant-cyan" />
            <span>EMA 20</span>
          </button>

          <button
            onClick={() => setShowEMA50(!showEMA50)}
            className={`flex items-center space-x-1.5 rounded-md border px-2.5 py-1 transition-all ${
              showEMA50
                ? "border-quant-amber/50 bg-quant-amber/10 text-quant-amber font-bold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-quant-amber" />
            <span>EMA 50</span>
          </button>

          <button
            onClick={() => setShowEMA200(!showEMA200)}
            className={`flex items-center space-x-1.5 rounded-md border px-2.5 py-1 transition-all ${
              showEMA200
                ? "border-quant-purple/50 bg-quant-purple/10 text-quant-purple font-bold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-quant-purple" />
            <span>EMA 200</span>
          </button>

          <button
            onClick={() => setShowVWAP(!showVWAP)}
            className={`flex items-center space-x-1.5 rounded-md border px-2.5 py-1 transition-all ${
              showVWAP
                ? "border-quant-blue/50 bg-quant-blue/10 text-quant-blue font-bold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-quant-blue" />
            <span>VWAP</span>
          </button>

          <button
            onClick={() => setShowBollinger(!showBollinger)}
            className={`flex items-center space-x-1.5 rounded-md border px-2.5 py-1 transition-all ${
              showBollinger
                ? "border-quant-cyan/50 bg-quant-cyan/10 text-white font-bold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            <span>Bollinger (20,2)</span>
          </button>

          <button
            onClick={() => setShowFibonacci(!showFibonacci)}
            className={`flex items-center space-x-1.5 rounded-md border px-2.5 py-1 transition-all ${
              showFibonacci
                ? "border-quant-amber/50 bg-quant-amber/10 text-quant-amber font-bold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            <span>Fibonacci</span>
          </button>
        </div>

        {/* Sub-pane Oscillator Switcher */}
        <div className="flex items-center space-x-1 border border-border rounded-lg bg-surface-card p-1 text-[11px]">
          <span className="text-gray-500 px-1.5">OSCILADOR:</span>
          <button
            onClick={() => setActiveOscillator("rsi")}
            className={`rounded px-2 py-0.5 ${
              activeOscillator === "rsi"
                ? "bg-quant-cyan/20 text-quant-cyan font-bold border border-quant-cyan/40"
                : "text-gray-400 hover:text-white"
            }`}
          >
            RSI 14
          </button>
          <button
            onClick={() => setActiveOscillator("macd")}
            className={`rounded px-2 py-0.5 ${
              activeOscillator === "macd"
                ? "bg-quant-blue/20 text-quant-blue font-bold border border-quant-blue/40"
                : "text-gray-400 hover:text-white"
            }`}
          >
            MACD (12,26,9)
          </button>
          <button
            onClick={() => setActiveOscillator("none")}
            className={`rounded px-2 py-0.5 ${
              activeOscillator === "none"
                ? "bg-surface text-gray-200"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            Ocultar
          </button>
        </div>
      </div>

      {/* Main Lightweight Charts Canvas */}
      <div className="relative rounded-xl border border-border bg-[#080B11] overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-background/70 backdrop-blur-sm text-xs font-mono text-quant-cyan space-x-2">
            <RefreshCw className="h-5 w-5 animate-spin" />
            <span>Calculando indicadores cuantitativos en Python...</span>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-background/80 p-4 text-xs font-mono text-quant-red">
            {error}
          </div>
        )}

        <div ref={chartContainerRef} className="w-full" />
      </div>

      {/* Oscillator Sub-Panel Canvas */}
      {activeOscillator !== "none" && (
        <div className="rounded-xl border border-border bg-[#080B11] p-2 overflow-hidden">
          <div className="flex items-center justify-between px-2 pb-1 text-[11px] font-mono text-gray-500">
            <span>
              {activeOscillator === "rsi" ? "RSI (14 Periodos - Wilder's Smoothing)" : "MACD (12, 26, 9) Divergence & Histogram"}
            </span>
            <span className="text-gray-400">Calculado en Backend Python</span>
          </div>
          <div ref={oscillatorContainerRef} className="w-full" />
        </div>
      )}

      {/* Indicator Values Telemetry Ribbon */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 text-[11px] font-mono border-t border-border pt-3">
          <div className="rounded border border-border bg-surface-card p-2">
            <div className="text-gray-500">ÚLTIMO PRECIO:</div>
            <div className="text-white font-bold">{data.bars[data.bars.length - 1]?.close.toFixed(2)}</div>
          </div>
          <div className="rounded border border-border bg-surface-card p-2">
            <div className="text-gray-500">EMA 20:</div>
            <div className="text-quant-cyan font-bold">
              {data.indicators.ema_20?.[data.indicators.ema_20.length - 1]?.toFixed(2) ?? "N/D"}
            </div>
          </div>
          <div className="rounded border border-border bg-surface-card p-2">
            <div className="text-gray-500">EMA 200:</div>
            <div className="text-quant-purple font-bold">
              {data.indicators.ema_200?.[data.indicators.ema_200.length - 1]?.toFixed(2) ?? "N/D"}
            </div>
          </div>
          <div className="rounded border border-border bg-surface-card p-2">
            <div className="text-gray-500">RSI 14:</div>
            <div className="text-quant-cyan font-bold">
              {data.indicators.rsi_14?.[data.indicators.rsi_14.length - 1]?.toFixed(2) ?? "N/D"}
            </div>
          </div>
          <div className="rounded border border-border bg-surface-card p-2">
            <div className="text-gray-500">ATR 14 (VOLATILIDAD):</div>
            <div className="text-quant-amber font-bold">
              {data.indicators.atr_14?.[data.indicators.atr_14.length - 1]?.toFixed(2) ?? "N/D"}
            </div>
          </div>
          <div className="rounded border border-border bg-surface-card p-2">
            <div className="text-gray-500">FIBONACCI 61.8%:</div>
            <div className="text-quant-amber font-bold">
              {data.indicators.fibonacci?.levels["0.618"]?.toFixed(2) ?? "N/D"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
