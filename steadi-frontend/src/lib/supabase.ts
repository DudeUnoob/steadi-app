import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://qciebchpdjxfumeoafwt.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjaWViY2hwZGp4ZnVtZW9hZnd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NDc2NTMsImV4cCI6MjA2MjMyMzY1M30.7hihI8t5_z7YFX_Yp9R4FgJYUvSFEOYix73Un-tWA0Y';

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables. Check your .env file.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey); 