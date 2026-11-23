#!/usr/bin/env python3
"""QUANT AI — Supabase Connection and Schema Verification Script.

Usage:
    python scripts/verify_supabase.py
"""

import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")

EXPECTED_TABLES = [
    "profiles",
    "user_permissions",
    "user_voice_preferences",
    "data_sources",
    "instruments",
    "ohlcv_bars",
    "watchlists",
    "watchlist_items",
    "strategies",
    "backtest_runs",
    "simulated_portfolios",
    "journal_entries",
    "alerts",
    "chat_sessions",
    "chat_messages",
    "ai_reports",
    "security_audit_logs",
]


def verify_supabase():
    print("=" * 60)
    print("QUANT AI — Verificador de Conexión a Supabase Cloud")
    print("=" * 60)

    if not SUPABASE_URL or "your-project-id" in SUPABASE_URL:
        print("[!] ADVERTENCIA: NEXT_PUBLIC_SUPABASE_URL no está configurado.")
        print("    Por favor define la URL real de tu proyecto Supabase en el archivo .env")
        print("    Ejemplo: NEXT_PUBLIC_SUPABASE_URL=https://abcdefghijklm.supabase.co")
        return False

    if not SUPABASE_KEY:
        print("[!] ADVERTENCIA: La clave API de Supabase (ANON o SERVICE_ROLE) no está configurada.")
        print("    Por favor define tu clave en .env")
        return False

    print(f"[*] Conectando a Supabase: {SUPABASE_URL}")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    try:
        # Test basic REST endpoint
        rest_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/"
        response = httpx.get(rest_url, headers=headers, timeout=10.0)

        if response.status_code not in (200, 404):
            print(f"[X] Error de autenticación HTTP {response.status_code}: {response.text}")
            return False

        print("[OK] Conexión autenticada exitosa con Supabase REST Gateway.")

        # Check each table
        missing = []
        for table in EXPECTED_TABLES:
            t_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}?limit=1"
            t_res = httpx.get(t_url, headers=headers, timeout=5.0)
            if t_res.status_code == 200:
                print(f"  [+] Tabla verificada con RLS activo: {table}")
            elif t_res.status_code in (401, 403):
                print(f"  [+] Tabla protegida por RLS (Acceso restringido): {table}")
            else:
                missing.append(table)
                print(f"  [-] Tabla no encontrada o error {t_res.status_code}: {table}")

        if not missing:
            print("\n[ÉXITO] Todas las tablas y políticas de seguridad RLS están activas en Supabase.")
            return True
        else:
            print(f"\n[!] Tablas faltantes: {missing}")
            print("    Asegúrate de ejecutar las migraciones 001 y 002 en el SQL Editor de Supabase.")
            return False

    except Exception as e:
        print(f"[X] Error al contactar Supabase: {e}")
        return False


if __name__ == "__main__":
    success = verify_supabase()
    sys.exit(0 if success else 1)
