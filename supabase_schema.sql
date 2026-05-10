-- AI Spend Audit - Supabase Schema
-- Run this in Supabase SQL Editor to create the required tables

-- Leads table: stores user email and company info
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    company_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audits table: stores each audit analysis
CREATE TABLE IF NOT EXISTS public.audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
    input_data JSONB NOT NULL,
    savings_data JSONB NOT NULL,
    ai_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_leads_email ON public.leads(email);
CREATE INDEX IF NOT EXISTS idx_audits_lead_id ON public.audits(lead_id);
CREATE INDEX IF NOT EXISTS idx_audits_created_at ON public.audits(created_at DESC);

-- Grant permissions to anon role
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT, INSERT, UPDATE ON public.leads TO anon;
GRANT SELECT, INSERT ON public.audits TO anon;
GRANT ALL ON public.leads TO anon;
GRANT ALL ON public.audits TO anon;

-- Enable Row Level Security
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audits ENABLE ROW LEVEL SECURITY;

-- RLS policies for anonymous access
DROP POLICY IF EXISTS "anon_all_leads" ON public.leads;
CREATE POLICY "anon_all_leads" ON public.leads FOR ALL TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_all_audits" ON public.audits;
CREATE POLICY "anon_all_audits" ON public.audits FOR ALL TO anon USING (true) WITH CHECK (true);
