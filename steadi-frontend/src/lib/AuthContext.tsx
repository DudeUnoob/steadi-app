import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { Session, User, AuthError } from '@supabase/supabase-js';
import { supabase } from './supabase';

// Define AuthStatus type for better state management
type AuthStatus = 'LOADING' | 'AUTHENTICATED' | 'UNAUTHENTICATED' | 'EMAIL_VERIFICATION_NEEDED';

type AuthContextType = {
  session: Session | null;
  user: User | null;
  status: AuthStatus;
  signIn: (email: string, password: string) => Promise<{
    error: AuthError | null;
    data: { session: Session | null; user: User | null } | null;
  }>;
  signInWithGoogle: () => Promise<void>;
  signUp: (email: string, password: string) => Promise<{
    error: AuthError | null;
    data: { session: Session | null; user: User | null } | null;
    needsEmailVerification: boolean;
  }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: AuthError | null }>;
  updatePassword: (password: string) => Promise<{ error: AuthError | null }>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('LOADING');

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setStatus(session ? 'AUTHENTICATED' : 'UNAUTHENTICATED');
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        console.log('Auth state changed:', event);
        setSession(session);
        setUser(session?.user ?? null);
        
        // Handle special cases for email verification
        if (event === 'SIGNED_IN') {
          setStatus('AUTHENTICATED');
        } else if (event === 'SIGNED_OUT') {
          setStatus('UNAUTHENTICATED');
        } else if (event === 'USER_UPDATED') {
          setStatus(session ? 'AUTHENTICATED' : 'UNAUTHENTICATED');
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    const response = await supabase.auth.signInWithPassword({ email, password });
    
    if (response.error) {
      setStatus('UNAUTHENTICATED');
    } else if (response.data.session) {
      setStatus('AUTHENTICATED');
    }
    
    return response;
  };

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  };

  const signUp = async (email: string, password: string) => {
    const response = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    
    // Check if email verification is needed
    const needsEmailVerification = !response.data.session && !response.error;
    
    if (needsEmailVerification) {
      setStatus('EMAIL_VERIFICATION_NEEDED');
    } else if (response.data.session) {
      setStatus('AUTHENTICATED');
    }
    
    return { ...response, needsEmailVerification };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    setStatus('UNAUTHENTICATED');
    
    // Clear any cached sync status
    localStorage.removeItem('supabase_sync_status');
  };
  
  const resetPassword = async (email: string) => {
    const response = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    });
    return response;
  };
  
  const updatePassword = async (password: string) => {
    const response = await supabase.auth.updateUser({ password });
    return response;
  };

  const value = {
    session,
    user,
    status,
    signIn,
    signInWithGoogle,
    signUp,
    signOut,
    resetPassword,
    updatePassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 