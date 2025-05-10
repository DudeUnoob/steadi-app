import { useState } from 'react';
import { useAuth } from '../../lib/AuthContext';

export function SignUpForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationSent, setVerificationSent] = useState(false);
  const { signUp, signInWithGoogle } = useAuth();

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setVerificationSent(false);
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      const { error, needsEmailVerification } = await signUp(email, password);
      
      if (error) {
        throw error;
      }
      
      if (needsEmailVerification) {
        setVerificationSent(true);
      }
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to sign up';
      
      if (errorMessage.includes('already registered')) {
        setError('This email is already registered. Please sign in instead.');
      } else if (errorMessage.includes('valid email')) {
        setError('Please enter a valid email address.');
      } else if (errorMessage.toLowerCase().includes('password')) {
        setError('Password is too weak. Please use at least 8 characters with a mix of letters, numbers, and symbols.');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setError(null);
    try {
      await signInWithGoogle();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to sign up with Google');
    }
  };

  if (verificationSent) {
    return (
      <div className="w-full max-w-md space-y-6 p-8 bg-white/10 backdrop-blur-sm rounded-lg border border-black/20">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-black font-['Poppins']">Check Your Email</h2>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-24 w-24 mx-auto my-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p className="mt-2 text-black/70 font-['Poppins']">
            We've sent a verification link to <strong>{email}</strong>
          </p>
          <p className="mt-6 text-black/70 font-['Poppins']">
            Please check your inbox and click the link to complete your signup.
          </p>
          <div className="mt-8">
            <p className="text-sm text-black/60 font-['Poppins']">
              Didn't receive an email? Check your spam folder or
              <button 
                onClick={() => setVerificationSent(false)}
                className="ml-1 text-black underline hover:text-black/80"
              >
                try again
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-6 p-8 bg-white/10 backdrop-blur-sm rounded-lg border border-black/20">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-black font-['Poppins']">Sign Up</h2>
        <p className="mt-2 text-black/70 font-['Poppins']">Create your account</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSignUp} className="space-y-4">
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
          <label htmlFor="password" className="block text-sm font-medium text-black font-['Poppins']">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white/20 border border-black/30 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-black/50"
          />
          <p className="mt-1 text-xs text-black/60">Must be at least 8 characters</p>
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-black font-['Poppins']">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="mt-1 block w-full px-3 py-2 bg-white/20 border border-black/30 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-black/50"
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white py-2 px-4 rounded-md hover:bg-black/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black font-['Poppins']"
          >
            {loading ? 'Signing up...' : 'Sign up'}
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
          onClick={handleGoogleSignUp}
          className="w-full flex items-center justify-center bg-white text-black py-2 px-4 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black/50 border border-black/20 font-['Poppins']"
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"
            />
          </svg>
          Sign up with Google
        </button>
      </div>
    </div>
  );
} 