import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjaWViY2hwZGp4ZnVtZW9hZnd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NDc2NTMsImV4cCI6MjA2MjMyMzY1M30.7hihI8t5_z7YFX_Yp9R4FgJYUvSFEOYix73Un-tWA0Y';

// Define a type for our headers to ensure consistency
type AuthHeaders = {
  'Content-Type': string;
  'Authorization'?: string;
  'apikey'?: string;
  'X-Debug-Auth'?: string;
};

// Track if sync has been attempted to avoid multiple sync attempts
let syncAttempted = false;
let lastSyncAttempt = 0;
const SYNC_RETRY_INTERVAL = 30000; // 30 seconds between sync attempts

// CRITICAL DEBUG: Force auth to true to bypass Supabase checks during debugging
// REMOVE THIS IN PRODUCTION!
const USE_DEBUG_AUTH = true;

// Debug token cache
let cachedToken = '';

// Simple helper function to get debug headers - ONLY FOR DEBUGGING
const getDebugHeaders = async (): Promise<AuthHeaders> => {
  // Try to use cached token first
  if (cachedToken) {
    console.log('Using cached debug token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${cachedToken}`,
      'apikey': SUPABASE_ANON_KEY,
      'X-Debug-Auth': 'true'
    };
  }
  
  // If no cached token, try to get one from Supabase
  try {
  const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      cachedToken = session.access_token;
      console.log('DEBUG MODE: Cached token from session for future use');
      return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${cachedToken}`,
        'apikey': SUPABASE_ANON_KEY,
        'X-Debug-Auth': 'true'
      };
    }
  } catch (e) {
    console.warn('Failed to get session in debug mode:', e);
  }
  
  // If we can't get a token from Supabase, use a content-type only header
  console.warn('DEBUG MODE: No token available, using debug header only');
  return {
    'Content-Type': 'application/json',
    'X-Debug-Auth': 'true'
  };
};

// Helper function to get auth headers
const getAuthHeaders = async (): Promise<AuthHeaders> => {
  // For debugging, bypass the normal flow
  if (USE_DEBUG_AUTH) {
    return getDebugHeaders();
  }

  try {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session || !session.access_token) {
      console.warn('No session or access token found');
      // Try to refresh the session
      const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
      
      if (refreshError || !refreshData.session) {
        console.error('Session refresh failed:', refreshError?.message);
        throw new Error('No authenticated session available');
      }
      
      console.log('Session refreshed successfully. New token expires at:', new Date(refreshData.session.expires_at! * 1000).toISOString());
      
      // Return headers with refreshed token
      return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshData.session.access_token}`,
        // Also include the apikey which might be required for Supabase operations
        'apikey': SUPABASE_ANON_KEY,
      };
    }
    
    // If we have a session, use the access token directly
    // Also, log token for debugging (first 10 chars only)
    const tokenPreview = session.access_token.substring(0, 10) + '...';
    const expiresAt = new Date(session.expires_at! * 1000);
    console.log(`Using access token: ${tokenPreview}, expires: ${expiresAt.toISOString()}`);
    
    // Cache the token for debug purposes
    cachedToken = session.access_token;
    
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`,
      // Include Supabase anon key if available
      'apikey': SUPABASE_ANON_KEY,
    };
  } catch (error: unknown) {
    console.error('Auth header retrieval error:', error instanceof Error ? error.message : error);
    // Return basic headers without auth token
    return {
      'Content-Type': 'application/json',
    };
  }
};

// Try direct authentication with the backend as a fallback if Supabase sync fails
const directBackendLogin = async (): Promise<boolean> => {
  // If in debug mode, always return success to bypass authentication
  if (USE_DEBUG_AUTH) {
    console.log('DEBUG MODE: Bypassing directBackendLogin, returning success');
    return true;
  }
  
  try {
    // Get Supabase session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session || !session.access_token) {
      console.error("No Supabase session available for direct backend login");
      return false;
    }
    
    // Try direct login with backend using Supabase user info
    const user = await supabase.auth.getUser(session.access_token);
    
    if (!user.data.user) {
      console.error("Could not retrieve user data from Supabase");
      return false;
    }
    
    // Attempt to directly create or sync user with backend
    const directSyncResponse = await fetch(`${API_URL}/supabase-auth/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
        'apikey': SUPABASE_ANON_KEY
      },
      body: JSON.stringify({
        supabase_id: user.data.user.id,
        email: user.data.user.email
      })
    });
    
    if (directSyncResponse.ok) {
      console.log("Direct backend login successful");
      syncAttempted = true;
      return true;
    } else {
      const errorText = await directSyncResponse.text();
      console.error("Direct backend login failed:", directSyncResponse.status, errorText);
      return false;
    }
  } catch (error: unknown) {
    console.error("Direct backend login error:", error instanceof Error ? error.message : error);
    return false;
  }
};

// Enhanced function to ensure we're authenticated before making API calls
const ensureAuthenticated = async () => {
  // In debug mode, bypass authentication
  if (USE_DEBUG_AUTH) {
    return true;
  }
  
  // Check if we have a valid session
  const { data: { session }, error } = await supabase.auth.getSession();
  
  if (error) {
    console.error('Session retrieval error:', error.message);
    throw new Error(`Authentication error: ${error.message}`);
  }
  
  if (!session) {
    // Redirect to login or show login modal
    console.error('No authenticated session. You need to log in.');
    throw new Error('Authentication required');
  }
  
  // Check if token is about to expire (within 5 minutes)
  const expiresAt = session.expires_at ? new Date(session.expires_at * 1000) : null;
  const now = new Date();
  const fiveMinutes = 5 * 60 * 1000; // 5 minutes in milliseconds
  
  if (expiresAt && (expiresAt.getTime() - now.getTime() < fiveMinutes)) {
    console.log('Token about to expire, refreshing...');
    const { data, error: refreshError } = await supabase.auth.refreshSession();
    
    if (refreshError) {
      console.error('Failed to refresh token:', refreshError.message);
      throw new Error(`Authentication failed: ${refreshError.message}`);
    }
    
    if (!data.session) {
      console.error('No session after refresh');
      throw new Error('Authentication required');
    }
    
    console.log('Token refreshed successfully. New expiry:', 
                new Date(data.session.expires_at! * 1000).toISOString());
  }
  
  return true;
};

// Non-blocking function to sync with backend auth
const attemptSupabaseSync = async (headers: AuthHeaders) => {
  // In debug mode, don't perform sync
  if (USE_DEBUG_AUTH) {
    console.log('DEBUG MODE: Bypassing auth sync');
    syncAttempted = true;
    return;
  }
  
  // Only attempt sync if we haven't tried recently
  const now = Date.now();
  if (syncAttempted && (now - lastSyncAttempt < SYNC_RETRY_INTERVAL)) {
    return;
  }
  
  lastSyncAttempt = now;
  
  try {
    console.log('Attempting to sync Supabase auth session...');
    // Set a timeout of 5 seconds for the sync request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${API_URL}/supabase-auth/sync`, {
      method: 'POST',
      headers,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      console.log('Supabase auth sync successful');
      syncAttempted = true;
      
      // Log the response for debugging
      try {
        const responseData = await response.json();
        console.log('Sync response data:', responseData);
      } catch (err) {
        console.log('No JSON response from sync endpoint');
      }
    } else {
      const statusText = response.statusText;
      console.warn(`Supabase auth sync failed with status ${response.status}: ${statusText}`);
      
      // If sync fails, try direct login as a fallback
      const directLoginSuccess = await directBackendLogin();
      if (directLoginSuccess) {
        console.log("Successfully authenticated with fallback method");
      } else {
        console.warn("Both sync methods failed. API calls may fail with auth errors.");
      }
    }
  } catch (error: unknown) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.warn('Supabase auth sync timed out after 5 seconds');
      
      // Try direct login if sync times out
      const directLoginSuccess = await directBackendLogin();
      if (directLoginSuccess) {
        console.log("Successfully authenticated with fallback method after timeout");
      }
    } else {
      console.warn('Supabase auth sync error:', error instanceof Error ? error.message : error);
    }
  }
};

// Try to authenticate immediately when this module loads
(async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session) {
      const headers = await getAuthHeaders();
      await attemptSupabaseSync(headers);
    }
  } catch (error) {
    console.warn("Initial auth sync failed:", error);
  }
})();

// Helper function to handle API responses
const handleApiResponse = async (response: Response, errorMessage: string) => {
  if (!response.ok) {
    // Try to parse error response as JSON
    let errorDetail = errorMessage;
    try {
      const errorData = await response.json();
      errorDetail = errorData?.detail || errorMessage;
      console.error('API error response:', errorData);
    } catch (e) {
      // If we can't parse as JSON, use status text
      errorDetail = `${errorMessage} (${response.status}: ${response.statusText})`;
    }
    
    // For 401 errors, reset sync attempted flag so we try again next time
    if (response.status === 401) {
      syncAttempted = false;
      console.warn('Authentication error. Will attempt to re-sync on next request.');
    }
    
    throw new Error(errorDetail);
  }
  
  return response.json();
};

// Dashboard API
export const dashboardApi = {
  getInventoryDashboard: async (search?: string, page: number = 1, limit: number = 50) => {
    try {
      // First ensure we have a valid session
      await ensureAuthenticated();
      
      // Now get the headers
      const headers = await getAuthHeaders();
      
      // Attempt auth sync in a non-blocking way
      attemptSupabaseSync(headers).catch(err => {
        console.error('Sync error (non-blocking):', err instanceof Error ? err.message : err);
      });
      
      const queryParams = new URLSearchParams();
      if (search) queryParams.append('search', search);
      queryParams.append('page', page.toString());
      queryParams.append('limit', limit.toString());
      
      // Add a timestamp to prevent caching
      queryParams.append('_ts', Date.now().toString());
      
      const url = `${API_URL}/dashboard/inventory?${queryParams}`;
      console.log('Fetching inventory from:', url);
      
      const response = await fetch(url, { 
        headers,
        // Add cache control to prevent caching
        cache: 'no-store' as RequestCache
      });
      
      // Log response status
      console.log('Inventory API response status:', response.status);
      
      return handleApiResponse(response, 'Failed to fetch inventory dashboard data');
    } catch (error: unknown) {
      console.error('Inventory dashboard fetch error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },
  
  getSalesAnalytics: async (period: number = 7) => {
    try {
      // First ensure we have a valid session
      await ensureAuthenticated();
      
      // Get the headers
      const headers = await getAuthHeaders();
      
      // Attempt auth sync in a non-blocking way
      attemptSupabaseSync(headers).catch(err => {
        console.error('Sync error (non-blocking):', err instanceof Error ? err.message : err);
      });
      
      const url = `${API_URL}/dashboard/analytics/sales?period=${period}&_ts=${Date.now()}`;
      console.log('Fetching sales analytics from:', url);
      
      const response = await fetch(url, { 
        headers,
        cache: 'no-store' as RequestCache
      });
      
      // Log response status
      console.log('Sales API response status:', response.status);
      
      return handleApiResponse(response, 'Failed to fetch sales analytics');
    } catch (error: unknown) {
      console.error('Sales analytics fetch error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },
};

// Products API
export const productsApi = {
  list: async () => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
      // Attempt auth sync in a non-blocking way
      attemptSupabaseSync(headers).catch(err => {
        console.error('Sync error (non-blocking):', err instanceof Error ? err.message : err);
      });
      
      const response = await fetch(`${API_URL}/edit/products`, { 
        headers,
        cache: 'no-store' as RequestCache
      });
      
      return handleApiResponse(response, 'Failed to fetch products');
    } catch (error: unknown) {
      console.error('Products fetch error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  create: async (data: any) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/products`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
      
      return handleApiResponse(response, 'Failed to create product');
    } catch (error: unknown) {
      console.error('Product create error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  update: async (id: string, data: any) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/products/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
      
      return handleApiResponse(response, 'Failed to update product');
    } catch (error: unknown) {
      console.error('Product update error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  delete: async (id: string) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/products/${id}`, {
      method: 'DELETE',
      headers,
    });
      
      return handleApiResponse(response, 'Failed to delete product');
    } catch (error: unknown) {
      console.error('Product delete error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },
};

// Suppliers API
export const suppliersApi = {
  list: async () => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
      // Attempt auth sync in a non-blocking way
      attemptSupabaseSync(headers).catch(err => {
        console.error('Sync error (non-blocking):', err instanceof Error ? err.message : err);
      });
      
      console.log('Fetching suppliers with headers:', {
        auth: headers.Authorization?.substring(0, 15) + '...',
        apikey: headers.apikey?.substring(0, 15) + '...'
      });
      
      const response = await fetch(`${API_URL}/edit/suppliers`, { 
        headers,
        cache: 'no-store' as RequestCache
      });
      
      console.log('Suppliers API response status:', response.status);
      
      return handleApiResponse(response, 'Failed to fetch suppliers');
    } catch (error: unknown) {
      console.error('Suppliers fetch error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  create: async (data: any) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/suppliers`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
      
      return handleApiResponse(response, 'Failed to create supplier');
    } catch (error: unknown) {
      console.error('Supplier create error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  update: async (id: string, data: any) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/suppliers/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
      
      return handleApiResponse(response, 'Failed to update supplier');
    } catch (error: unknown) {
      console.error('Supplier update error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  delete: async (id: string) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/suppliers/${id}`, {
      method: 'DELETE',
      headers,
    });
      
      return handleApiResponse(response, 'Failed to delete supplier');
    } catch (error: unknown) {
      console.error('Supplier delete error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },
};

// Sales API
export const salesApi = {
  list: async () => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
      // Attempt auth sync in a non-blocking way
      attemptSupabaseSync(headers).catch(err => {
        console.error('Sync error (non-blocking):', err instanceof Error ? err.message : err);
      });
      
      const response = await fetch(`${API_URL}/edit/sales`, { 
        headers,
        cache: 'no-store' as RequestCache
      });
      
      return handleApiResponse(response, 'Failed to fetch sales');
    } catch (error: unknown) {
      console.error('Sales fetch error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  create: async (data: any) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/sales`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
      
      return handleApiResponse(response, 'Failed to create sale');
    } catch (error: unknown) {
      console.error('Sale create error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  update: async (id: string, data: any) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/sales/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
      
      return handleApiResponse(response, 'Failed to update sale');
    } catch (error: unknown) {
      console.error('Sale update error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },

  delete: async (id: string) => {
    try {
      await ensureAuthenticated();
    const headers = await getAuthHeaders();
      
    const response = await fetch(`${API_URL}/edit/sales/${id}`, {
      method: 'DELETE',
      headers,
    });
      
      return handleApiResponse(response, 'Failed to delete sale');
    } catch (error: unknown) {
      console.error('Sale delete error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },
}; 