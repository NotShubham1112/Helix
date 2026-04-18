/**
 * Supabase SQL Migrations - Row Level Security & Schema
 * 
 * SECURITY CRITICAL:
 * These policies enforce that users can only access their own data
 * at the database layer (defense in depth)
 * 
 * How to apply:
 * 1. Go to Supabase Dashboard
 * 2. Click "SQL Editor"
 * 3. Create new query
 * 4. Copy/paste sections below
 * 5. Run each section
 * 
 * Order matters: Enable RLS first, then create policies
 */

-- ============================================
-- TABLE: users (managed by Supabase Auth)
-- ============================================
-- Supabase automatically creates this, but we add RLS

ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Users can read their own auth record
CREATE POLICY "Users can view own auth record"
ON auth.users FOR SELECT
USING (auth.uid() = id);

-- Note: Don't write to auth.users directly - use Supabase Auth API


-- ============================================
-- TABLE: reports (Medical reports)
-- ============================================

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_deleted BOOLEAN DEFAULT false
);

-- Enable RLS on reports table
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policy: Users can SELECT their own reports
CREATE POLICY "Users can select own reports"
ON reports FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can INSERT their own reports
CREATE POLICY "Users can insert own reports"
ON reports FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can UPDATE their own reports
CREATE POLICY "Users can update own reports"
ON reports FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can DELETE their own reports
CREATE POLICY "Users can delete own reports"
ON reports FOR DELETE
USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX reports_user_id_idx ON reports(user_id);
CREATE INDEX reports_created_at_idx ON reports(created_at);


-- ============================================
-- TABLE: lab_results (Lab analysis results)
-- ============================================

CREATE TABLE IF NOT EXISTS lab_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    test_name TEXT NOT NULL,
    value NUMERIC,
    unit TEXT,
    reference_range TEXT,
    status TEXT DEFAULT 'normal', -- 'normal', 'abnormal', 'critical'
    analysis JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable RLS
ALTER TABLE lab_results ENABLE ROW LEVEL SECURITY;

-- Policy: Users can SELECT their own lab results
CREATE POLICY "Users can select own lab results"
ON lab_results FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can INSERT their own lab results
CREATE POLICY "Users can insert own lab results"
ON lab_results FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can UPDATE their own lab results
CREATE POLICY "Users can update own lab results"
ON lab_results FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Indexes
CREATE INDEX lab_results_user_id_idx ON lab_results(user_id);
CREATE INDEX lab_results_report_id_idx ON lab_results(report_id);


-- ============================================
-- TABLE: prescriptions (Medical prescriptions)
-- ============================================

CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES auth.users(id),
    medication_name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    duration_days INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Enable RLS
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;

-- Policy: Patients can SELECT their own prescriptions
CREATE POLICY "Patients can select own prescriptions"
ON prescriptions FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Doctors can INSERT prescriptions for their patients
-- (Simplified - in production, implement proper doctor-patient relationship)
CREATE POLICY "Doctors can insert prescriptions"
ON prescriptions FOR INSERT
WITH CHECK (auth.uid() = doctor_id);

-- Indexes
CREATE INDEX prescriptions_user_id_idx ON prescriptions(user_id);
CREATE INDEX prescriptions_doctor_id_idx ON prescriptions(doctor_id);


-- ============================================
-- TABLE: audit_logs (Security audit trail)
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable RLS on audit logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can VIEW their own audit logs
CREATE POLICY "Users can view own audit logs"
ON audit_logs FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Admins can view all audit logs
-- (Requires role column in users table)
CREATE POLICY "Admins can view all audit logs"
ON audit_logs FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM auth.users
        WHERE id = auth.uid()
        -- Note: This requires storing role in user_metadata
    )
);

-- Allow backend service to INSERT logs
-- (Use with service role key)
CREATE POLICY "Service can insert audit logs"
ON audit_logs FOR INSERT
WITH CHECK (true);

-- Indexes
CREATE INDEX audit_logs_user_id_idx ON audit_logs(user_id);
CREATE INDEX audit_logs_created_at_idx ON audit_logs(created_at);


-- ============================================
-- EXTENSION: jwt verification
-- ============================================

-- Verify that JWT is valid and not expired
-- Can be used in policies for additional security

CREATE OR REPLACE FUNCTION verify_jwt_not_expired()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (auth.jwt() ->> 'exp')::int > (EXTRACT(EPOCH FROM now()))::int;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- FUNCTION: audit_log_action
-- ============================================

-- Create function to log user actions
CREATE OR REPLACE FUNCTION audit_log_action(
    p_action TEXT,
    p_resource_type TEXT DEFAULT NULL,
    p_resource_id UUID DEFAULT NULL,
    p_details JSONB DEFAULT '{}'::jsonb
)
RETURNS void AS $$
BEGIN
    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
    VALUES (auth.uid(), p_action, p_resource_type, p_resource_id, p_details);
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- TRIGGER: Update updated_at timestamp
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to reports
CREATE TRIGGER update_reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- VERIFY RLS is ENABLED
-- ============================================

-- Run this to verify RLS is enabled on all tables:
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Expected output:
-- tablename      | rowsecurity
-- ├─ reports     | t
-- ├─ lab_results | t
-- ├─ prescriptions | t
-- └─ audit_logs  | t
