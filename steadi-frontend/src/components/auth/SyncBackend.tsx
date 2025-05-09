import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../lib/AuthContext';
import { supabase } from '../../lib/supabase';

// Base URL for API calls
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Maximum number of retry attempts
const MAX_RETRIES = 3;
// Delay between retries (milliseconds)
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

    // Don't retry more than MAX_RETRIES times
    if (retryCount >= MAX_RETRIES) {
      console.error('Max retries reached when syncing with backend');
      setError('Failed to sync user data after multiple attempts');
      return;
    }

    try {
      // Get a fresh token before making the request
      const { data: { session: freshSession } } = await supabase.auth.getSession();
      const token = freshSession?.access_token;
      
      if (!token) {
        throw new Error('No valid token available');
      }
      
      // Add additional data like email and Supabase ID from user object
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

      // Reset error and retries on success
      setError(null);
      setRetryCount(0);
      setSynced(true);
      
      // Store sync status in localStorage to avoid unnecessary syncs during the session
      localStorage.setItem('supabase_sync_status', JSON.stringify({
        userId: user.id,
        timestamp: Date.now()
      }));
      
    } catch (err) {
      console.error('Error syncing with backend:', err);
      setError(err instanceof Error ? err.message : 'Sync error');
      
      // Increment retry count
      setRetryCount(prev => prev + 1);
      
      // Schedule a retry
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

    // Check if we've already synced this user recently
    const syncStatus = localStorage.getItem('supabase_sync_status');
    if (syncStatus) {
      try {
        const { userId, timestamp } = JSON.parse(syncStatus);
        const syncAge = Date.now() - timestamp;
        
        // If we've synced this user in the last hour and it's the same user, skip
        if (userId === user.id && syncAge < 3600000) {
          setSynced(true);
          return;
        }
      } catch (e) {
        // Invalid JSON in localStorage, ignore and proceed with sync
      }
    }

    // Start sync process
    syncUser();
  }, [session, user, synced, syncUser]);

  // This component doesn't render anything visible
  return null;
} 