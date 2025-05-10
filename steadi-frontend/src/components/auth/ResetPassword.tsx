import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../lib/AuthContext';

export function ResetPassword() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const { updatePassword, user } = useAuth();

  if (user && !localStorage.getItem('sb-recovery-token')) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

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
      const { error } = await updatePassword(password);
      if (error) throw error;
      
      localStorage.removeItem('sb-recovery-token');
      
      setSuccess(true);
      startCountdown();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  const startCountdown = () => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  if (success && countdown === 0) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex flex-col">
      
      <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center">
          <h1 className="text-4xl font-light text-black font-['Poppins']">Steadi.</h1>
        </div>
      </nav>

      <div className="flex-grow flex flex-col justify-center items-center p-6">
        <div className="w-full max-w-md space-y-6 p-8 bg-white/10 backdrop-blur-sm rounded-lg border border-black/20">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-black font-['Poppins']">Reset Password</h2>
            <p className="mt-2 text-black/70 font-['Poppins']">
              {success ? 'Your password has been reset successfully!' : 'Create a new password for your account'}
            </p>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {success ? (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded text-center">
              <p>Password updated successfully!</p>
              <p className="mt-2">Redirecting to dashboard in {countdown} seconds...</p>
            </div>
          ) : (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-black font-['Poppins']">
                  New Password
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
                  Confirm New Password
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
                  {loading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
} 