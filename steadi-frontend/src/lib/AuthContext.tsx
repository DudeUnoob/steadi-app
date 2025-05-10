import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { Session, User, AuthError } from '@supabase/supabase-js';
import { supabase } from './supabase';

// Base URL for API calls
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Define AuthStatus type for better state management
type AuthStatus = 'LOADING' | 'AUTHENTICATED' | 'UNAUTHENTICATED' | 'EMAIL_VERIFICATION_NEEDED';

// Generic type for auth responses
type AuthResponseType = {
  data: any;
  error: AuthError | null;
};

type AuthContextType = {
  session: Session | null;
  user: User | null;
  status: AuthStatus;
  signIn: (email: string, password: string) => Promise<AuthResponseType>;
  signInWithGoogle: () => Promise<void>;
  signUp: (email: string, password: string) => Promise<AuthResponseType & { needsEmailVerification?: boolean }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<AuthResponseType>;
  updatePassword: (password: string) => Promise<AuthResponseType>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Define useAuth hook at the top level to make it compatible with Fast Refresh
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

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
    try {
      // Notify backend about logout
      if (session?.access_token) {
        try {
          await fetch(`${API_URL}/supabase-auth/logout`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`,
            }
          });
          console.log('Backend notified about logout');
        } catch (error) {
          // Log error but continue with logout process
          console.error('Failed to notify backend about logout:', error);
        }
      }

      // Sign out from Supabase
      await supabase.auth.signOut();
      setStatus('UNAUTHENTICATED');
      
      // Clear any cached sync status
      localStorage.removeItem('supabase_sync_status');
    } catch (error) {
      console.error('Error during sign out:', error);
      // Still set status to unauthenticated even if there was an error
      setStatus('UNAUTHENTICATED');
    }
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