import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../lib/AuthContext';
import { supabase } from '../../lib/supabase';


const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MAX_RETRIES = 3;
const RETRY_DELAY = 2000;

export function SyncBackend() {
  const { session, user } = useAuth();
  const [synced, setSynced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const syncUser = useCallback(async () => {
    if (!session || !user) {
      return;
    }

    if (retryCount >= MAX_RETRIES) {
      console.error('Max retries reached when syncing with backend');
      setError('Failed to sync user data after multiple attempts');
      return;
    }

    try {
      const { data: { session: freshSession } } = await supabase.auth.getSession();
      const token = freshSession?.access_token;
      
      if (!token) {
        throw new Error('No valid token available');
      }
      
      const userData = {
        email: user.email,
        supabase_id: user.id
      };

      const response = await fetch(`${API_URL}/supabase-auth/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(userData)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to sync with backend');
      }

      setError(null);
      setRetryCount(0);
      setSynced(true);
      
      localStorage.setItem('supabase_sync_status', JSON.stringify({
        userId: user.id,
        timestamp: Date.now()
      }));
      
    } catch (err) {
      console.error('Error syncing with backend:', err);
      setError(err instanceof Error ? err.message : 'Sync error');
      
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