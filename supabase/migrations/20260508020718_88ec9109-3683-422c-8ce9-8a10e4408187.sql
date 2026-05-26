
CREATE SCHEMA IF NOT EXISTS extensions;
DROP INDEX IF EXISTS public.foods_search_idx;
ALTER EXTENSION pg_trgm SET SCHEMA extensions;
CREATE INDEX foods_search_idx ON public.foods USING gin (search extensions.gin_trgm_ops);

CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END; $$;
