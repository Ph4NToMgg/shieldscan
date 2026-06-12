import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Debug: check what actually got baked into the build
console.log('[Supabase] URL:', supabaseUrl);
console.log('[Supabase] Key length:', supabaseAnonKey?.length ?? 'UNDEFINED');
console.log('[Supabase] Key prefix:', supabaseAnonKey?.substring(0, 10) ?? 'UNDEFINED');

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('[Supabase] CRITICAL: Missing env vars! VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is not set.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
