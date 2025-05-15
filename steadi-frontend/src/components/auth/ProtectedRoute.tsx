import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../lib/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requireRulesCompleted?: boolean;
}

export function ProtectedRoute({ 
  children, 
  requireRulesCompleted = true 
}: ProtectedRouteProps) {
  const { status, isRulesSetupRequired } = useAuth();
  const location = useLocation();

  useEffect(() => {
    // Check if user is at rules page but should not be
    if (
      location.pathname.includes('/auth/rules') && 
      !isRulesSetupRequired() &&
      localStorage.getItem('rules_setup_completed') === 'true'
    ) {
      // User already completed setup but is trying to access rules page again
      window.location.href = '/dashboard';
    }
  }, [location.pathname, isRulesSetupRequired]);

  // Show loading state
  if (status === 'LOADING') {
    return (
      <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex justify-center items-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg border border-black/20 p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-black mx-auto"></div>
          <p className="mt-4 text-black font-['Poppins']">Loading...</p>
        </div>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (status === 'UNAUTHENTICATED') {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  // If email verification needed, show message or redirect
  if (status === 'EMAIL_VERIFICATION_NEEDED') {
    return <Navigate to="/auth/verify-email" state={{ from: location }} replace />;
  }

  // If rules setup required and the current page is not the rules page
  if (status === 'RULES_SETUP_REQUIRED' && !location.pathname.includes('/auth/rules')) {
    return <Navigate to="/auth/rules" state={{ from: location }} replace />;
  }

  // If at dashboard but rules setup is required
  if (requireRulesCompleted && isRulesSetupRequired()) {
    return <Navigate to="/auth/rules" state={{ from: location }} replace />;
  }

  // Render children if all conditions pass
  return <>{children}</>;
} 