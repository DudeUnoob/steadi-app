import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { supabase } from '../../lib/supabase';
import { UserRole } from '@/lib/AuthContext';

export function AuthCallback() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [redirectPath, setRedirectPath] = useState<string>('/dashboard');
  const location = useLocation();

  useEffect(() => {
   
    const handleCallback = async () => {
      try {
        setLoading(true);
        
        const isPasswordReset = location.hash.includes('type=recovery');
        
        if (isPasswordReset) {
          const accessToken = new URLSearchParams(location.hash.substring(1)).get('access_token');
          if (!accessToken) {
            throw new Error('No access token found in URL');
          }
          
          localStorage.setItem('sb-recovery-token', accessToken);
          setRedirectPath('/auth/reset-password');
        } else {
          // Get the session and user data
          const { data, error } = await supabase.auth.getSession();
          if (error) {
            throw error;
          }
          
          if (data.session) {
            // Get user metadata to determine the role
            const { data: userData } = await supabase.auth.getUser();
            
            // Check if this appears to be a new OAuth user (no role in metadata)
            const isOAuthUser = userData?.user?.app_metadata?.provider === 'google';
            const hasRole = !!userData?.user?.user_metadata?.role;
            
            if (isOAuthUser && !hasRole) {
              // New OAuth user without a role, redirect to role selection
              console.log('New OAuth user detected, redirecting to role selection');
              // Clear organization ID for new users to ensure they go through the proper flow
              localStorage.removeItem('organization_id');
              setRedirectPath('/auth/role-selection');
            } else {
              // Existing user or user with role already set
              const role = userData?.user?.user_metadata?.role || 'staff';
              
              // Store the role for later use
              localStorage.setItem('user_role', role);
              
              // Set appropriate flags and redirect based on role
              if (role === UserRole.OWNER) {
                // Owner needs to set up rules
                localStorage.setItem('rules_setup_required', 'true');
                localStorage.setItem('rules_setup_completed', 'false');
                localStorage.setItem('org_code_required', 'false');
                setRedirectPath('/auth/rules');
              } else {
                // Staff and Manager need to enter organization code
                localStorage.setItem('rules_setup_required', 'false');
                localStorage.setItem('org_code_required', 'true');
                setRedirectPath('/auth/organization');
              }
            }
          }
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error processing auth callback:', err);
        setError(err instanceof Error ? err.message : 'Authentication error');
        setLoading(false);
      }
    };

    handleCallback();
  }, [location]);

  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex justify-center items-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg border border-black/20 p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-black mx-auto"></div>
          <p className="mt-4 text-black font-['Poppins']">Verifying your authentication...</p>
        </div>
      </div>
    );
  }

 
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex flex-col justify-center items-center p-6">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg border border-black/20 p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold text-black mb-4 font-['Poppins']">Authentication Error</h2>
          <p className="text-black mb-6 font-['Poppins']">{error}</p>
          <a
            href="/auth"
            className="block w-full bg-black text-white py-2 px-4 rounded-md text-center"
          >
            Return to Sign In
          </a>
        </div>
      </div>
    );
  }

 
  return <Navigate to={redirectPath} replace />;
} 