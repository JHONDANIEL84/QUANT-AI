-- =====================================================================
-- QUANT AI — SUPABASE POSTGRESQL RLS SECURITY HARDENING (002)
-- Fase 14: Seguridad, Políticas de Acceso y Aislamiento Multi-inquilino
-- =====================================================================

-- 1. Ensure RLS is enabled on all sensitive tables
ALTER TABLE IF EXISTS public.strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.backtest_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.user_voice_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.ai_reports ENABLE ROW LEVEL SECURITY;

-- 2. Strategies RLS: Strict user isolation
DROP POLICY IF EXISTS "Users can manage own strategies" ON public.strategies;
CREATE POLICY "Users can manage own strategies" ON public.strategies
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 3. Backtest Runs RLS: Strict user isolation
DROP POLICY IF EXISTS "Users can manage own backtest runs" ON public.backtest_runs;
CREATE POLICY "Users can manage own backtest runs" ON public.backtest_runs
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 4. Alerts RLS: Strict user isolation
DROP POLICY IF EXISTS "Users can manage own alerts" ON public.alerts;
CREATE POLICY "Users can manage own alerts" ON public.alerts
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 5. User Permissions: Read own permissions, admin write
DROP POLICY IF EXISTS "Users can view own permissions" ON public.user_permissions;
CREATE POLICY "Users can view own permissions" ON public.user_permissions
    FOR SELECT
    USING (auth.uid() = user_id);

-- 6. User Voice Preferences: Strict user isolation
DROP POLICY IF EXISTS "Users can manage own voice preferences" ON public.user_voice_preferences;
CREATE POLICY "Users can manage own voice preferences" ON public.user_voice_preferences
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 7. AI Reports: Strict user isolation
DROP POLICY IF EXISTS "Users can manage own ai reports" ON public.ai_reports;
CREATE POLICY "Users can manage own ai reports" ON public.ai_reports
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ---------------------------------------------------------------------
-- 8. SECURITY AUDIT LOGGING TABLE
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.security_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

ALTER TABLE public.security_audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own audit logs" ON public.security_audit_logs;
CREATE POLICY "Users can view own audit logs" ON public.security_audit_logs
    FOR SELECT
    USING (auth.uid() = user_id);

-- ---------------------------------------------------------------------
-- 9. AUTO-PROVISIONING TRIGGER ON NEW USER SIGNUP
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, preferred_currency, timezone)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        'COP',
        'America/Bogota'
    )
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO public.user_permissions (user_id, role)
    VALUES (NEW.id, 'trader')
    ON CONFLICT DO NOTHING;

    INSERT INTO public.user_voice_preferences (user_id, voice_name)
    VALUES (NEW.id, 'es-CO-Standard-A')
    ON CONFLICT DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
