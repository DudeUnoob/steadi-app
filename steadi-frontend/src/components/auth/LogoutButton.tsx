import { useAuth } from '../../lib/AuthContext';
import { useNavigate } from 'react-router-dom';
import { IconLogout } from '@tabler/icons-react';

type LogoutButtonProps = {
  variant?: 'icon' | 'text' | 'full';
  className?: string;
};

export function LogoutButton({ 
  variant = 'full', 
  className = '' 
}: LogoutButtonProps) {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  
  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };
  
  if (variant === 'icon') {
    return (
      <button
        onClick={handleLogout}
        className={`text-black hover:text-black/70 ${className}`}
        aria-label="Logout"
      >
        <IconLogout size={20} />
      </button>
    );
  }
  
  if (variant === 'text') {
    return (
      <button
        onClick={handleLogout}
        className={`text-black hover:text-black/70 font-['Poppins'] ${className}`}
      >
        Logout
      </button>
    );
  }
  
  return (
    <button
      onClick={handleLogout}
      className={`flex items-center gap-2 text-black hover:text-black/70 font-['Poppins'] ${className}`}
    >
      <IconLogout size={20} />
      <span>Logout</span>
    </button>
  );
} 