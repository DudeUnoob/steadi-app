import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../lib/AuthContext';

export function ProtectedRoute() {
  const { user, status } = useAuth();

  if (status === 'LOADING') {
    return (
      <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex justify-center items-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-black"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  return <Outlet />;
} 