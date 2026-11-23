"""QUANT AI - Fase 14: Security, RLS & Deployment Verification Tests."""

import os
from pathlib import Path
from backend.core.config import settings
from backend.schemas.system import HealthResponse


def test_migration_files_and_rls_policies():
    """Verify SQL migrations exist and strictly enforce Row Level Security."""
    base_dir = Path(__file__).resolve().parent.parent
    migration_dir = base_dir / "database" / "migrations"
    m1 = migration_dir / "001_initial_schema.sql"
    m2 = migration_dir / "002_security_rls_hardening.sql"

    assert m1.exists(), "001_initial_schema.sql must exist"
    assert m2.exists(), "002_security_rls_hardening.sql must exist"

    sql_content = m2.read_text(encoding="utf-8")

    # Assert RLS is enabled for user-owned tables
    sensitive_tables = [
        "strategies",
        "backtest_runs",
        "alerts",
        "user_permissions",
        "user_voice_preferences",
        "ai_reports",
        "security_audit_logs",
    ]
    for table in sensitive_tables:
        assert f"ALTER TABLE IF EXISTS public.{table} ENABLE ROW LEVEL SECURITY;" in sql_content or \
               f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;" in sql_content, (
            f"Table {table} must have ROW LEVEL SECURITY explicitly enabled."
        )

    # Assert user isolation via auth.uid() = user_id
    assert "USING (auth.uid() = user_id)" in sql_content
    assert "security_audit_logs" in sql_content
    assert "handle_new_user" in sql_content


def test_core_security_and_localization_settings():
    """Verify system defaults adhere to Colombian financial and timezone standards."""
    assert settings.DEFAULT_CURRENCY == "COP"
    assert settings.DEFAULT_TIMEZONE == "America/Bogota"
    assert "QUANT AI" in settings.APP_NAME
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_deployment_artifacts_integrity():
    """Verify Docker, Compose, and Vercel production deployment configurations."""
    base_dir = Path(__file__).resolve().parent.parent

    # Backend Dockerfile
    dockerfile = base_dir / "Dockerfile"
    assert dockerfile.exists(), "Root Dockerfile must exist for backend packaging"
    df_content = dockerfile.read_text(encoding="utf-8")
    assert "USER quantuser" in df_content, "Backend container must run as non-root user"
    assert "HEALTHCHECK" in df_content, "Backend container must declare healthcheck"

    # Docker Compose
    compose_file = base_dir / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml must exist"
    dc_content = compose_file.read_text(encoding="utf-8")
    assert "quant_ai_backend" in dc_content
    assert "quant_ai_frontend" in dc_content

    # Frontend Dockerfile
    fe_dockerfile = base_dir / "frontend" / "Dockerfile"
    assert fe_dockerfile.exists(), "frontend/Dockerfile must exist"

    # Frontend Vercel configuration
    vercel_file = base_dir / "frontend" / "vercel.json"
    assert vercel_file.exists(), "frontend/vercel.json must exist"
    v_content = vercel_file.read_text(encoding="utf-8")
    assert "X-Frame-Options" in v_content
    assert "X-Content-Type-Options" in v_content
