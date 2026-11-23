# Guía de Despliegue en Producción — QUANT AI

Esta guía detalla los pasos para conectar la infraestructura Cloud: **Supabase** (PostgreSQL & Auth), **Vercel** (Frontend Next.js) y **Render / Railway / VPS** (Backend FastAPI).

---

## 1. Configuración de Supabase (Base de Datos & RLS)

### Paso 1.1: Crear Proyecto en Supabase
1. Ingresa a [supabase.com](https://supabase.com) y crea un nuevo proyecto.
2. Selecciona la región más cercana (ej. `East US` o `South America - São Paulo`).
3. Guarda tu contraseña de base de datos.

### Paso 1.2: Ejecutar las Migraciones SQL
En el panel de control de Supabase, ve a **SQL Editor** -> **New Query** y ejecuta en orden:
1. Contenido de `database/migrations/001_initial_schema.sql` (Crea las 22 tablas base y RLS inicial).
2. Contenido de `database/migrations/002_security_rls_hardening.sql` (Endurecimiento RLS para estrategias, auditoría y triggers).
3. (Opcional) Contenido de `database/seed/initial_seed.sql` para cargar fuentes de datos y activos precargados (BTCUSDT, ETHUSDT, AAPL, ECOPETROL, etc.).

### Paso 1.3: Obtener Claves API
En Supabase, ve a **Project Settings** -> **API**:
- Copia la **Project URL** (`https://<project-id>.supabase.co`).
- Copia la **anon (public) key**.
- Copia la **service_role (secret) key**.

Colócalas en tu `.env`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://<project-id>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
```

Verifica la conexión ejecutando:
```bash
python scripts/verify_supabase.py
```

---

## 2. Despliegue del Backend FastAPI (Render / Railway / Docker)

### Opción A: Render (Recomendada con `render.yaml`)
1. Ve a [render.com](https://render.com) y conecta tu repositorio `JHONDANIEL84/QUANT-AI`.
2. El archivo [render.yaml](../render.yaml) provisionará automáticamente el servicio web Docker.
3. En las variables de entorno de Render, añade:
   - `AI_API_KEY`: Tu clave de Google Gemini (obtenida en [Google AI Studio](https://aistudio.google.com/)).
   - `NEXT_PUBLIC_SUPABASE_URL` y claves de Supabase.
   - `CORS_ORIGINS`: `["https://tu-frontend.vercel.app"]`
4. Copia la URL pública generada por Render (ej. `https://quant-ai-backend.onrender.com`).

### Opción B: Docker en VPS propio
```bash
docker-compose up -d --build
```

---

## 3. Despliegue del Frontend (Vercel)

1. Ingresa a [vercel.com](https://vercel.com) e importa el repositorio `JHONDANIEL84/QUANT-AI`.
2. **Root Directory:** Selecciona `frontend`.
3. **Environment Variables:** Añade:
   - `NEXT_PUBLIC_API_URL`: URL del backend de Render (ej. `https://quant-ai-backend.onrender.com`).
   - `NEXT_PUBLIC_SUPABASE_URL`: Tu URL de Supabase.
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Tu anon key de Supabase.
   - `NEXT_PUBLIC_DEFAULT_CURRENCY`: `COP`
   - `NEXT_PUBLIC_DEFAULT_TIMEZONE`: `America/Bogota`
4. Haz clic en **Deploy**. Vercel compilará automáticamente con las reglas de seguridad de [vercel.json](../frontend/vercel.json).
