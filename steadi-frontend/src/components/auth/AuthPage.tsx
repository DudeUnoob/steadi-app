import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../lib/AuthContext';
import { LoginForm } from './LoginForm';
import { SignUpForm } from './SignUpForm';

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const { user, loading } = useAuth();

  // If the user is already logged in, redirect to dashboard
  if (user && !loading) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex flex-col">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center">
          <h1 className="text-4xl font-light text-black font-['Poppins']">Steadi.</h1>
        </div>
      </nav>

      {/* Auth Container */}
      <div className="flex-grow flex flex-col justify-center items-center p-6">
        {mode === 'login' ? <LoginForm /> : <SignUpForm />}

        <div className="mt-6 text-center">
          <p className="text-black font-['Poppins']">
            {mode === 'login' ? "Don't have an account?" : "Already have an account?"}
            <button
              onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
              className="ml-2 text-black font-medium underline hover:text-black/80"
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
} 