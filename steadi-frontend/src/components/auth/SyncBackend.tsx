import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../lib/AuthContext';
import { supabase } from '../../lib/supabase';


const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MAX_RETRIES = 3;
const RETRY_DELAY = 2000;

export function SyncBackend() {
  const { session, user } = useAuth();
  const [synced, setSynced] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const syncUser = useCallback(async () => {
    if (!session || !user) {
      return;
    }

    if (retryCount >= MAX_RETRIES) {
      console.error('Max retries reached when syncing with backend');
      return;
    }

    try {
      const { data: { session: freshSession } } = await supabase.auth.getSession();
      const token = freshSession?.access_token;
      
      if (!token) {
        throw new Error('No valid token available');
      }
      
      // Get stored role from localStorage if available
      const storedRole = localStorage.getItem('user_role');
      
      const userData = {
        email: user.email,
        supabase_id: user.id,
        ...(storedRole ? { role: storedRole } : {})
      };

      console.log('Syncing user data with backend:', { ...userData, token: '***' });

      const response = await fetch(`${API_URL}/supabase-auth/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(userData)
      });

      // Clone the response so we can read it twice
      const responseClone = response.clone();
      
      try {
        const responseText = await responseClone.text();
        console.log('Raw backend response:', responseText);
      } catch (err) {
        // Just log the error and continue
        console.error('Error reading raw response:', err);
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to sync with backend');
      }

      const syncedUserData = await response.json().catch(() => ({}));
      console.log('Synced with backend successfully:', syncedUserData);
      
      // Update local role if it changed in the backend
      if (syncedUserData.role && (!storedRole || storedRole !== syncedUserData.role)) {
        localStorage.setItem('user_role', syncedUserData.role);
        console.log('Updated local role from backend:', syncedUserData.role);
      }

      setRetryCount(0);
      setSynced(true);
      
      localStorage.setItem('supabase_sync_status', JSON.stringify({
        userId: user.id,
        timestamp: Date.now()
      }));
      
    } catch (err) {
      console.error('Error syncing with backend:', err);
      
      setRetryCount(prev => prev + 1);
      
      setTimeout(() => {
        if (session && user) {
          syncUser();
        }
      }, RETRY_DELAY);
    }
  }, [session, user, retryCount]);

  useEffect(() => {
    if (!session || !user || synced) {
      return;
    }

    const syncStatus = localStorage.getItem('supabase_sync_status');
    if (syncStatus) {
      try {
        const { userId, timestamp } = JSON.parse(syncStatus);
        const syncAge = Date.now() - timestamp;
        
        if (userId === user.id && syncAge < 3600000) {
          setSynced(true);
          return;
        }
      } catch (e) {
        
      }
    }

    
    syncUser();
  }, [session, user, synced, syncUser]);

  return null;
} 