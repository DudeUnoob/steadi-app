import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { supabase } from '../../lib/supabase';

export function AuthCallback() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    // Process the OAuth callback or email link
    const handleCallback = async () => {
      try {
        setLoading(true);
        
        // Check if this is a password reset callback
        const isPasswordReset = location.hash.includes('type=recovery');
        
        // Check if this is an email verification callback
        const isEmailVerification = location.hash.includes('type=signup');
        
        if (isPasswordReset) {
          // Extract token from URL
          const accessToken = new URLSearchParams(location.hash.substring(1)).get('access_token');
          if (!accessToken) {
            throw new Error('No access token found in URL');
          }
          
          // Store the token so we can use it on the password reset page
          localStorage.setItem('sb-recovery-token', accessToken);
          
          // Navigate to the reset password page will happen via the redirect after this completes
        } else {
          // Handle regular sign-in callback (OAuth or email verification)
          const { error } = await supabase.auth.getSession();
          if (error) {
            throw error;
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

  // Show loading indicator
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

  // Show error if something went wrong
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

  // Check if this is a password reset
  if (location.hash.includes('type=recovery')) {
    return <Navigate to="/auth/reset-password" replace />;
  }

  // Redirect to dashboard on success
  return <Navigate to="/dashboard" replace />;
} 