import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { supabase } from '../../lib/supabase';

export function AuthCallback() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
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
          
         
        } else {
         
          const { error } = await supabase.auth.getSession();
          if (error) {
            throw error;
          }
          
          // Mark that user needs to complete rules setup
          localStorage.setItem('rules_setup_required', 'true');
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

 
  if (location.hash.includes('type=recovery')) {
    return <Navigate to="/auth/reset-password" replace />;
  }

 
  return <Navigate to="/auth/rules" replace />;
} 