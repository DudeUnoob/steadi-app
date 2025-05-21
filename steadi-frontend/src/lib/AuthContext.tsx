import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { Session, User, AuthError, Provider } from '@supabase/supabase-js';
import { supabase } from './supabase';

// Base URL for API calls
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Define AuthStatus type for better state management
type AuthStatus = 'LOADING' | 'AUTHENTICATED' | 'UNAUTHENTICATED' | 'EMAIL_VERIFICATION_NEEDED' | 'RULES_SETUP_REQUIRED';

// Generic type for auth responses
type AuthResponseType = {
  data: any;
  error: AuthError | null;
};

// User role type
export const UserRole = {
  OWNER: "owner",
  MANAGER: "manager",
  STAFF: "staff"
} as const;

export type UserRoleType = typeof UserRole[keyof typeof UserRole];

type AuthContextType = {
  session: Session | null;
  user: User | null;
  status: AuthStatus;
  signIn: (email: string, password: string) => Promise<AuthResponseType>;
  signInWithGoogle: () => Promise<void>;
  signUp: (email: string, password: string, role?: UserRoleType) => Promise<AuthResponseType & { needsEmailVerification?: boolean }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<AuthResponseType>;
  updatePassword: (password: string) => Promise<AuthResponseType>;
  isRulesSetupRequired: () => boolean;
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
  const [userRole, setUserRole] = useState<UserRoleType | null>(null);

  // Check if rules setup is required
  const isRulesSetupRequired = () => {
    return localStorage.getItem('rules_setup_required') === 'true' && 
           localStorage.getItem('rules_setup_completed') !== 'true';
  };

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      
      // Check if user needs to complete rules setup
      if (session) {
        // Try to get role from localStorage
        const storedRole = localStorage.getItem('user_role');
        if (storedRole) {
          setUserRole(storedRole as UserRoleType);
        }
        
        if (isRulesSetupRequired()) {
          setStatus('RULES_SETUP_REQUIRED');
        } else {
          setStatus('AUTHENTICATED');
        }
      } else {
        setStatus('UNAUTHENTICATED');
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        console.log('Auth state changed:', event);
        setSession(session);
        setUser(session?.user ?? null);
        
        // Handle special cases for email verification
        if (event === 'SIGNED_IN') {
          // Check if user needs to complete rules setup
          if (isRulesSetupRequired()) {
            setStatus('RULES_SETUP_REQUIRED');
          } else {
            setStatus('AUTHENTICATED');
          }
        } else if (event === 'SIGNED_OUT') {
          setStatus('UNAUTHENTICATED');
          setUserRole(null);
        } else if (event === 'USER_UPDATED') {
          if (session) {
            // Check if user needs to complete rules setup
            if (isRulesSetupRequired()) {
              setStatus('RULES_SETUP_REQUIRED');
            } else {
              setStatus('AUTHENTICATED');
            }
          } else {
            setStatus('UNAUTHENTICATED');
          }
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
      // Check if user needs to complete rules setup
      if (isRulesSetupRequired()) {
        setStatus('RULES_SETUP_REQUIRED');
      } else {
        setStatus('AUTHENTICATED');
      }
      
      // Sync with backend to get user role
      await syncWithBackend(response.data.session.access_token);
    }
    
    return response;
  };

  const signInWithGoogle = async () => {
    // Clear any previous flags to ensure fresh state for Google auth
    localStorage.removeItem('rules_setup_required');
    localStorage.removeItem('rules_setup_completed');
    localStorage.removeItem('org_code_required');
    
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  };

  // Sync user with backend
  const syncWithBackend = async (token: string, role?: UserRoleType) => {
    try {
      const userData = role ? { role } : {};
      
      const response = await fetch(`${API_URL}/supabase-auth/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(userData)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.role) {
          localStorage.setItem('user_role', data.role);
          setUserRole(data.role as UserRoleType);
        }
      } else {
        console.error('Failed to sync user with backend');
      }
    } catch (error) {
      console.error('Error syncing with backend:', error);
    }
  };

  const signUp = async (email: string, password: string, role: UserRoleType = UserRole.STAFF) => {
    // Save role in localStorage for later use
    localStorage.setItem('user_role', role);
    setUserRole(role);
    
    const response = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
        data: {
          role: role // Store role in Supabase user metadata
        }
      },
    });
    
    // Check if email verification is needed
    const needsEmailVerification = !response.data.session && !response.error;
    
    if (needsEmailVerification) {
      setStatus('EMAIL_VERIFICATION_NEEDED');
    } else if (response.data.session) {
      // Set appropriate flags based on user role
      if (role === UserRole.OWNER) {
        // Owner needs to set up rules
        localStorage.setItem('rules_setup_required', 'true');
        localStorage.setItem('rules_setup_completed', 'false');
        setStatus('RULES_SETUP_REQUIRED');
      } else {
        // Staff and Manager should provide organization code instead
        localStorage.setItem('rules_setup_required', 'false');
        localStorage.setItem('org_code_required', 'true');
        setStatus('AUTHENTICATED'); // Will be redirected to org code page by router
      }
      
      // Sync with backend, passing the role
      await syncWithBackend(response.data.session.access_token, role);
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
      
      // Verify the session is cleared
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        console.warn('Session still exists after logout, forcing cleanup');
        // Force session cleanup if still exists
        await supabase.auth.signOut({ scope: 'local' });
      }
      
      setStatus('UNAUTHENTICATED');
      setSession(null);
      setUser(null);
      setUserRole(null);
      
      // Clear any cached sync status and local storage items
      localStorage.removeItem('supabase_sync_status');
      localStorage.removeItem('rules_setup_required');
      localStorage.removeItem('rules_setup_completed');
      localStorage.removeItem('user_role');
      
      // Additional cleanup for any other potential auth data
      sessionStorage.clear(); // Clear any session storage data
      
      console.log('Logout completed successfully');
    } catch (error) {
      console.error('Error during sign out:', error);
      // Still set status to unauthenticated even if there was an error
      setStatus('UNAUTHENTICATED');
      setSession(null);
      setUser(null);
      setUserRole(null);
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
    isRulesSetupRequired,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
} 