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
const USE_DEBUG_AUTH = false;

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
    // Get Supabase session
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
      
      // Exchange Supabase token for backend token
      const exchangeResponse = await fetch(`${API_URL}/supabase-auth/token`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshData.session.access_token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!exchangeResponse.ok) {
        throw new Error('Failed to exchange token with backend');
      }
      
      const tokenData = await exchangeResponse.json();
      
      return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${tokenData.access_token}`,
        'apikey': SUPABASE_ANON_KEY,
      };
    }
    
    // Exchange Supabase token for backend token
    const exchangeResponse = await fetch(`${API_URL}/supabase-auth/token`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!exchangeResponse.ok) {
      throw new Error('Failed to exchange token with backend');
    }
    
    const tokenData = await exchangeResponse.json();
    
    // Cache the token for debug purposes
    cachedToken = tokenData.access_token;
    
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${tokenData.access_token}`,
      'apikey': SUPABASE_ANON_KEY,
    };
  } catch (error) {
    console.error('Auth header retrieval error:', error instanceof Error ? error.message : error);
    throw new Error('Could not validate credentials - token processing issue');
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

// Helper to handle API responses
const handleApiResponse = async (response: Response, errorMessage: string = 'API request failed') => {
  if (!response.ok) {
    // First try to get a structured error response
    try {
      const errorData = await response.json();
      
      // Handle common error status codes with specific messages
      if (response.status === 422) {
        // Unprocessable Entity - often related to validation errors
        const detail = errorData.detail || 'Invalid data format';
        // Check if this might be a UUID/SKU confusion
        if (detail.includes('UUID') || detail.includes('not found') || detail.includes('id')) {
          throw new Error(`${detail} - Make sure you're using the product's UUID and not its SKU.`);
        }
        throw new Error(detail);
      }
      
      if (response.status === 404) {
        throw new Error(errorData.detail || 'Resource not found');
      }
      
      if (response.status === 401 || response.status === 403) {
        throw new Error(errorData.detail || 'Authentication or authorization failed');
      }
      
      // Use the API's error message if available
      if (errorData.detail) {
        throw new Error(errorData.detail);
      } else if (errorData.error) {
        throw new Error(errorData.error);
      } else if (errorData.message) {
        throw new Error(errorData.message);
      }
    } catch (parseError) {
      // If we can't parse the error as JSON, use the status text
      if (parseError instanceof Error && !parseError.message.includes('JSON')) {
        throw parseError;
      }
      throw new Error(`${errorMessage} (${response.status}: ${response.statusText})`);
    }
  }
  
  // Handle empty successful responses (e.g., DELETE operations)
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch (err) {
      console.warn('Empty JSON response', err);
      return {}; // Return empty object for empty JSON responses
    }
  }
  
  return {}; // Default to empty object for non-JSON responses
}

// Dashboard API
export const dashboardApi = {
  getInventoryDashboard: async (search?: string, page: number = 1, limit: number = 50, retryCount: number = 0): Promise<any> => {
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
      console.log('Using headers:', {
        contentType: headers['Content-Type'],
        authType: headers['Authorization'] ? 'Bearer Token' : 'None',
        debugAuth: headers['X-Debug-Auth'] || 'None',
      });
      
      // Set a timeout for the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const response = await fetch(url, { 
          headers,
          // Add cache control to prevent caching
          cache: 'no-store' as RequestCache,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Log response status
        console.log('Inventory API response status:', response.status);
        
        return handleApiResponse(response, 'Failed to fetch inventory dashboard data');
      } catch (fetchError) {
        clearTimeout(timeoutId);
        
        // Check if it's an abort error (timeout)
        if (fetchError instanceof DOMException && fetchError.name === 'AbortError') {
          throw new Error('Request timed out. The server took too long to respond.');
        }
        
        // Network error (e.g., server not running, CORS issues)
        if (fetchError instanceof TypeError && fetchError.message === 'Failed to fetch') {
          // Implement retry logic for network errors, but limit to 3 retries
          if (retryCount < 3) {
            console.log(`Network error, retrying (${retryCount + 1}/3)...`);
            // Wait a bit before retrying (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
            return dashboardApi.getInventoryDashboard(search, page, limit, retryCount + 1);
          }
          
          throw new Error(
            'Network error: Unable to connect to the server. ' +
            'Please check if the backend server is running and CORS is properly configured.'
          );
        }
        
        // Rethrow other fetch errors
        throw fetchError;
      }
    } catch (error: unknown) {
      console.error('Inventory dashboard fetch error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },
  
  getSalesAnalytics: async (period: number = 7, retryCount: number = 0): Promise<any> => {
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
      console.log('Using headers:', {
        contentType: headers['Content-Type'],
        authType: headers['Authorization'] ? 'Bearer Token' : 'None',
        debugAuth: headers['X-Debug-Auth'] || 'None',
      });
      
      // Set a timeout for the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const response = await fetch(url, { 
          headers,
          cache: 'no-store' as RequestCache,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Log response status
        console.log('Sales API response status:', response.status);
        
        return handleApiResponse(response, 'Failed to fetch sales analytics');
      } catch (fetchError) {
        clearTimeout(timeoutId);
        
        // Check if it's an abort error (timeout)
        if (fetchError instanceof DOMException && fetchError.name === 'AbortError') {
          throw new Error('Request timed out. The server took too long to respond.');
        }
        
        // Network error handling with retry logic
        if (fetchError instanceof TypeError && fetchError.message === 'Failed to fetch') {
          if (retryCount < 3) {
            console.log(`Network error, retrying (${retryCount + 1}/3)...`);
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
            return dashboardApi.getSalesAnalytics(period, retryCount + 1);
          }
          
          throw new Error(
            'Network error: Unable to connect to the server. ' +
            'Please check if the backend server is running and CORS is properly configured.'
          );
        }
        
        throw fetchError;
      }
    } catch (error: unknown) {
      console.error('Sales analytics fetch error:', error instanceof Error ? error.message : error);
      throw error;
    }
  },
  
  getSales: async (
    period: number = 7, 
    productId?: string, 
    page: number = 1, 
    limit: number = 50, 
    retryCount: number = 0
  ): Promise<any> => {
    try {
      // First ensure we have a valid session
      await ensureAuthenticated();
      
      // Get the headers
      const headers = await getAuthHeaders();
      
      // Attempt auth sync in a non-blocking way
      attemptSupabaseSync(headers).catch(err => {
        console.error('Sync error (non-blocking):', err instanceof Error ? err.message : err);
      });
      
      // Build query parameters
      const queryParams = new URLSearchParams();
      queryParams.append('period', period.toString());
      if (productId) queryParams.append('product_id', productId);
      queryParams.append('page', page.toString());
      queryParams.append('limit', limit.toString());
      queryParams.append('_ts', Date.now().toString()); // Prevent caching
      
      const url = `${API_URL}/dashboard/sales?${queryParams}`;
      console.log('Fetching sales data from:', url);
      
      // Set a timeout for the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const response = await fetch(url, { 
          headers,
          cache: 'no-store' as RequestCache,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Log response status
        console.log('Sales data API response status:', response.status);
        
        return handleApiResponse(response, 'Failed to fetch sales data');
      } catch (fetchError) {
        clearTimeout(timeoutId);
        
        // Check if it's an abort error (timeout)
        if (fetchError instanceof DOMException && fetchError.name === 'AbortError') {
          throw new Error('Request timed out. The server took too long to respond.');
        }
        
        // Network error handling with retry logic
        if (fetchError instanceof TypeError && fetchError.message === 'Failed to fetch') {
          if (retryCount < 3) {
            console.log(`Network error, retrying (${retryCount + 1}/3)...`);
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
            return dashboardApi.getSales(period, productId, page, limit, retryCount + 1);
          }
          
          throw new Error(
            'Network error: Unable to connect to the server. ' +
            'Please check if the backend server is running and CORS is properly configured.'
          );
        }
        
        throw fetchError;
      }
    } catch (error: unknown) {
      console.error('Sales data fetch error:', error instanceof Error ? error.message : error);
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
      
      // Validate that SKU is not a UUID format
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (data.sku && uuidPattern.test(data.sku)) {
        throw new Error("SKU cannot be in UUID format. Please use a descriptive alphanumeric code.");
      }
      
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
      
      // Ensure ID is a valid UUID format
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!id || !uuidPattern.test(id)) {
        throw new Error("Invalid product ID format. The system requires a UUID.");
      }
      
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
      
      // Ensure ID is a valid UUID format
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!id || !uuidPattern.test(id)) {
        throw new Error("Invalid product ID format. The system requires a UUID.");
      }
      
      console.log(`Attempting to delete product with ID: ${id}`);
      
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
      
      console.log(`Attempting to delete supplier with ID: ${id}`);
      
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
      
      console.log(`Attempting to delete sale with ID: ${id}`);
      
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