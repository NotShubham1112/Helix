-- Helix Healthcare Backend Database Schema
-- Tables: reports, analysis, chat_messages
-- With Row-Level Security (RLS) for user isolation

-- Enable pgvector for future vector search
CREATE EXTENSION IF NOT EXISTS vector;

-- Reports Table
CREATE TABLE IF NOT EXISTS public.reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    file_name text NOT NULL,
    file_url text,
    parsed_data jsonb NOT NULL DEFAULT '{}'::jsonb,
    analysis_result jsonb,
    status text DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS reports_user_id_idx ON public.reports (user_id);
CREATE INDEX IF NOT EXISTS reports_created_at_idx ON public.reports (created_at DESC);
CREATE INDEX IF NOT EXISTS reports_status_idx ON public.reports (status);

-- Analysis Table
CREATE TABLE IF NOT EXISTS public.analysis (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES public.reports (id) ON DELETE CASCADE,
    user_id uuid NOT NULL,
    result jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS analysis_report_id_idx ON public.analysis (report_id);
CREATE INDEX IF NOT EXISTS analysis_user_id_idx ON public.analysis (user_id);
CREATE INDEX IF NOT EXISTS analysis_created_at_idx ON public.analysis (created_at DESC);

-- Chat Messages Table
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES public.reports (id) ON DELETE CASCADE,
    user_id uuid NOT NULL,
    message text NOT NULL,
    response text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS chat_messages_report_id_idx ON public.chat_messages (report_id);
CREATE INDEX IF NOT EXISTS chat_messages_user_id_idx ON public.chat_messages (user_id);
CREATE INDEX IF NOT EXISTS chat_messages_created_at_idx ON public.chat_messages (created_at DESC);

-- Vector Memory Table (for RAG)
CREATE TABLE IF NOT EXISTS public.vector_memory (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    report_id uuid REFERENCES public.reports (id) ON DELETE CASCADE,
    text text NOT NULL,
    embedding vector(384),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS vector_memory_user_id_idx ON public.vector_memory (user_id);
CREATE INDEX IF NOT EXISTS vector_memory_report_id_idx ON public.vector_memory (report_id);

-- Row Level Security Policies
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vector_memory ENABLE ROW LEVEL SECURITY;

-- Reports RLS: Users can only see their own reports
CREATE POLICY reports_select_policy ON public.reports
    FOR SELECT
    USING (auth.uid()::text = user_id::text);

CREATE POLICY reports_insert_policy ON public.reports
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY reports_update_policy ON public.reports
    FOR UPDATE
    USING (auth.uid()::text = user_id::text);

CREATE POLICY reports_delete_policy ON public.reports
    FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- Analysis RLS
CREATE POLICY analysis_select_policy ON public.analysis
    FOR SELECT
    USING (auth.uid()::text = user_id::text);

CREATE POLICY analysis_insert_policy ON public.analysis
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

-- Chat Messages RLS
CREATE POLICY chat_select_policy ON public.chat_messages
    FOR SELECT
    USING (auth.uid()::text = user_id::text);

CREATE POLICY chat_insert_policy ON public.chat_messages
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY chat_delete_policy ON public.chat_messages
    FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- Vector Memory RLS
CREATE POLICY vector_memory_select_policy ON public.vector_memory
    FOR SELECT
    USING (auth.uid()::text = user_id::text);

CREATE POLICY vector_memory_insert_policy ON public.vector_memory
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY vector_memory_delete_policy ON public.vector_memory
    FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- Storage Buckets (create manually in Supabase console)
-- CREATE BUCKET reports (public=false)
-- Bucket RLS: Users can only access their own files (/{user_id}/*)
