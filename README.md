# QUANT AI — Intelligent Quantitative Swing Trading & AI Analysis Platform

> **Nivel:** Profesional Avanzado | **Idioma:** Español | **Moneda:** COP | **Zona Horaria:** America/Bogota  
> **Mercados:** Acciones, ETFs, Criptomonedas, Bolsa de Valores de Colombia (BVC)

QUANT AI es una plataforma integral de swing trading y análisis cuantitativo construida sobre datos trazables, cálculos reproducibles, identificación objetiva de liquidez, Smart Money Concepts (SMC) y un asistente de inteligencia artificial contextual con capacidades de visión de pantalla y voz en tiempo real.

---

## 🛠️ Stack Tecnológico

- **Frontend:** Next.js 14 (App Router), React 18, TypeScript estricto, Tailwind CSS, Lightweight Charts, Zustand, TanStack Query, Lucide Icons.
- **Backend:** Python 3.10+, FastAPI, Pydantic 2, Pandas, NumPy, SciPy, scikit-learn, Uvicorn, uv.
- **Base de Datos & Auth:** Supabase PostgreSQL con Row Level Security (RLS) en 22 entidades de negocio.
- **Datos de Mercado:** Yahoo Finance (`yfinance`), Binance Public REST & WebSockets, Adaptador CSV BVC, Adaptador Macroeconómico (BanRep, DANE, FRED).
- **Inteligencia Artificial:** Módulo desacoplado para LLMs, reconocimiento de voz (STT), síntesis de voz (TTS) y análisis visual de pantalla.

---

## 📁 Estructura del Monorepositorio

```
quant-ai/
├── frontend/                   # Aplicación Web Next.js 14
│   ├── app/                    # App Router, Layouts y Páginas
│   ├── components/             # Navbar, Telemetría, Rastreador de Fases, Gráficos
│   ├── hooks/                  # Custom React Hooks
│   ├── lib/                    # Utilidades y formateadores (COP, USD)
│   ├── services/               # Clientes API para FastAPI
│   └── types/                  # Definiciones TypeScript de datos y telemetría
│
├── backend/                    # Servidor FastAPI y Core Cuantitativo
│   ├── api/v1/                 # Endpoints (/health, /system/status, etc.)
│   ├── core/                   # Configuración (pydantic-settings), Errores globales
│   ├── schemas/                # Schemas Pydantic de entrada y salida
│   └── main.py                 # Punto de entrada de la aplicación FastAPI
│
├── quantitative_engine/        # Motor Matemático y Estadístico Independiente
│   ├── indicators/             # Indicadores técnicos vectorizados (EMA, RSI, MACD, etc.)
│   ├── candles/                # Detección de patrones de velas japonesas
│   ├── market_structure/       # Identificación de HH, HL, LH, LL y Swings
│   ├── price_action/           # Soportes, Resistencias, Pullbacks, Retesteos
│   ├── smc/                    # BOS, CHOCH, Order Blocks, FVGs, Mitigación
│   ├── liquidity/              # Liquidity Intelligence, Equal Highs/Lows, Sweeps
│   ├── fibonacci/              # Niveles de retroceso y extensión
│   ├── volatility/             # Medición de volatilidad histórica y ATR
│   ├── risk/                   # Dimensionamiento de posición y gestión de riesgo
│   └── backtesting/            # Motor de simulación histórica sin look-ahead bias
│
├── data_providers/             # Capa Abstraída de Proveedores de Mercado
│   ├── base/                   # BaseMarketDataProvider y modelos MarketBar normalizados
│   ├── yahoo/                  # Adaptador Yahoo Finance (Acciones US y ETFs)
│   ├── binance/                # Adaptador Binance REST y WebSocket (Cripto)
│   ├── bvc/                    # Adaptador de archivos CSV para acciones colombianas
│   └── macro/                  # Adaptador macroeconómico (BanRep, DANE, FRED)
│
├── ai_engine/                  # Capa de Inteligencia Artificial Multimodal
│   ├── chat/                   # Asistente contextual con inyección de estado de mercado
│   ├── context/                # Ensamblador de contexto técnico y cuantitativo
│   ├── vision/                 # Analizador de capturas de pantalla
│   ├── speech_to_text/         # Transcripción de audio a texto
│   ├── text_to_speech/         # Síntesis vocal en español
│   └── orchestration/          # Orquestador del modo combinado Live Assistant
│
├── database/                   # Definición de Esquema y Migraciones Supabase
│   ├── migrations/             # 001_initial_schema.sql (22 tablas con RLS)
│   └── seed/                   # initial_seed.sql (Instrumentos y fuentes preconfigurados)
│
├── tests/                      # Suite de pruebas automatizadas (pytest)
├── docs/                       # Documentación y especificaciones de arquitectura
└── .github/workflows/          # Integración Continua (CI) en GitHub Actions
```

---

## 🚀 Puesta en Marcha Local

### 1. Requisitos Previos
- Node.js >= 20.x y npm
- Python >= 3.10
- [uv](https://astral.sh/uv) (Gestor de paquetes ultrarrápido para Python)

### 2. Configurar Variables de Entorno
```bash
cp .env.example .env
```

### 3. Backend (FastAPI + uv)
```bash
# Crear entorno virtual e instalar dependencias
uv venv
uv pip install -e ".[dev]"

# Ejecutar pruebas unitarias
.venv/bin/pytest -v tests/

# Iniciar servidor de desarrollo
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Documentación OpenAPI interactiva disponible en: `http://localhost:8000/docs`

### 4. Frontend (Next.js)
```bash
cd frontend
npm install
npm run typecheck
npm run dev
```
Aplicación disponible en: `http://localhost:3000`

---

## 📋 Plan Maestro de 14 Fases

- [x] **Fase 1:** Arquitectura y Configuración Inicial (Completada y verificada)
- [ ] **Fase 2:** Proveedores de Datos (Yahoo Finance, Binance WS, BVC CSV, Macro)
- [ ] **Fase 3:** Gráficos e Indicadores (Lightweight Charts + cálculos vectorizados)
- [ ] **Fase 4:** Price Action y Estructura de Mercado
- [ ] **Fase 5:** Smart Money Concepts (BOS, CHOCH, OB, FVG)
- [ ] **Fase 6:** Módulo Avanzado: Liquidity Intelligence & Sweeps
- [ ] **Fase 7:** Scanner de Mercados y Análisis Multitemporal
- [ ] **Fase 8:** Gestión del Riesgo y Portafolio Simulado en COP
- [ ] **Fase 9:** Backtesting Lab y Validación Fuera de Muestra
- [ ] **Fase 10:** QUANT AI Analyst — Chat Inteligente Contextual
- [ ] **Fase 11:** Asistente Visual — Live Screen Analysis
- [ ] **Fase 12:** Asistente de Voz — QUANT AI Voice (STT & TTS)
- [ ] **Fase 13:** Modo Combinado: Live Voice + Live Vision Assistant
- [ ] **Fase 14:** Seguridad, Pruebas Integrales y Despliegue en Producción
