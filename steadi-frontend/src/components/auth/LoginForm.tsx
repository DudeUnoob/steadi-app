import { useState } from 'react';
import { useAuth } from '../../lib/AuthContext';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forgotPassword, setForgotPassword] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const { signIn, signInWithGoogle, resetPassword } = useAuth();

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const { error } = await signIn(email, password);
      if (error) {
        // Handle specific error cases with user-friendly messages
        const errorMessage = error.message;
        
        if (errorMessage.includes('Invalid login credentials')) {
          throw new Error('Incorrect email or password. Please try again.');
        } else if (errorMessage.includes('Email not confirmed')) {
          throw new Error('Please verify your email address before signing in.');
        } else {
          throw error;
        }
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to sign in');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    try {
      await signInWithGoogle();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to sign in with Google');
    }
  };
  
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your email address.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const { error } = await resetPassword(email);
      if (error) throw error;
      setResetSent(true);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };
  
  // Show password reset form
  if (forgotPassword) {
    return (
      <div className="w-full max-w-md space-y-6 p-8 bg-white/10 backdrop-blur-sm rounded-lg border border-black/20">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-black font-['Poppins']">Reset Password</h2>
          <p className="mt-2 text-black/70 font-['Poppins']">
            {resetSent 
              ? `Password reset email sent to ${email}` 
              : 'Enter your email to receive a password reset link'}
          </p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        {resetSent ? (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            Please check your email for the password reset link.
          </div>
        ) : (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-black font-['Poppins']">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 bg-white/20 border border-black/30 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-black/50"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-black text-white py-2 px-4 rounded-md hover:bg-black/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black font-['Poppins']"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </div>
          </form>
        )}
        
        <button
          onClick={() => {
            setForgotPassword(false);
            setResetSent(false);
            setError(null);
          }}
          className="w-full mt-4 text-black text-sm hover:underline font-['Poppins']"
        >
          Back to Sign In
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-6 p-8 bg-white/10 backdrop-blur-sm rounded-lg border border-black/20">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-black font-['Poppins']">Login</h2>
        <p className="mt-2 text-black/70 font-['Poppins']">Sign in to your account</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleEmailLogin} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-black font-['Poppins']">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white/20 border border-black/30 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-black/50"
            placeholder="your@email.com"
          />
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="block text-sm font-medium text-black font-['Poppins']">
              Password
            </label>
            <button
              type="button"
              onClick={() => setForgotPassword(true)}
              className="text-sm text-black hover:underline font-['Poppins']"
            >
              Forgot password?
            </button>
          </div>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white/20 border border-black/30 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-black/50"
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white py-2 px-4 rounded-md hover:bg-black/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black font-['Poppins']"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </div>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-black/30"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-gradient-to-r from-[#ff5757] to-[#8c52ff] text-black font-['Poppins']">
            Or continue with
          </span>
        </div>
      </div>

      <div>
        <button
          onClick={handleGoogleLogin}
          className="w-full flex items-center justify-center bg-white text-black py-2 px-4 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black/50 border border-black/20 font-['Poppins']"
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"
            />
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  );
} 