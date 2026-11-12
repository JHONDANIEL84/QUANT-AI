export type MarketType = "stock" | "etf" | "crypto" | "forex" | "index" | "macro";
export type DataStatus = "realtime" | "delayed" | "historical" | "provisional" | "incomplete";

export interface MarketBar {
  symbol: string;
  market: MarketType;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
  interval: string;
  downloaded_at: string;
  data_status: DataStatus;
  trades_count?: number;
  quote_volume?: number;
  is_closed: boolean;
}

export interface TickerSnapshot {
  symbol: string;
  market: MarketType;
  price: number;
  change_24h: number;
  change_24h_percent: number;
  high_24h?: number;
  low_24h?: number;
  volume_24h?: number;
  source: string;
  data_status: DataStatus;
  timestamp: string;
  currency: string;
}

export interface OrderBookLevel {
  price: number;
  quantity: number;
}

export interface OrderBookDepth {
  symbol: string;
  source: string;
  timestamp: string;
  best_bid: number;
  best_ask: number;
  spread: number;
  spread_percentage: number;
  imbalance_ratio: number;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  total_bid_volume: number;
  total_ask_volume: number;
  data_status: DataStatus;
}

export interface MacroIndicator {
  country: string;
  indicator_code: string;
  name: string;
  value: number;
  unit: string;
  period: string;
  publication_date: string;
  source: string;
  is_official: boolean;
}

export interface ProviderHealth {
  source: string;
  symbol?: string;
  is_connected: boolean;
  data_status: DataStatus;
  last_update: string;
  latency_ms: number;
  notes?: string;
}
