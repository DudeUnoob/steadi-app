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

// Add request caching and deduplication
const requestCache = new Map<string, { data: any; timestamp: number; promise?: Promise<any> }>();
const pendingRequests = new Map<string, Promise<any>>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const STALE_WHILE_REVALIDATE_TTL = 30 * 60 * 1000; // 30 minutes

// Token management improvements
let tokenRefreshPromise: Promise<string> | null = null;
let lastTokenRefresh = 0;
const TOKEN_REFRESH_INTERVAL = 50 * 60 * 1000; // 50 minutes

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
  
  // Check if we need to refresh token proactively
  const now = Date.now();
  if (now - lastTokenRefresh > TOKEN_REFRESH_INTERVAL && !tokenRefreshPromise) {
    tokenRefreshPromise = refreshAuthToken();
    try {
      await tokenRefreshPromise;
      lastTokenRefresh = now;
    } finally {
      tokenRefreshPromise = null;
    }
  }
  
  // Check if we have a valid session
  const { data: { session }, error } = await supabase.auth.getSession();
  
  if (error) {
    console.error('Supabase session error:', error.message);
    throw new Error('Authentication failed - session error');
  }
  
  if (!session) {
    console.error('No active session found');
    throw new Error('No authenticated session available');
  }
  
  // Check if token is about to expire (within 10 minutes)
  const expiresAt = session.expires_at;
  const tokenExpiresIn = (expiresAt! * 1000) - Date.now();
  
  if (tokenExpiresIn < 10 * 60 * 1000) { // Less than 10 minutes
    console.log('Token expires soon, refreshing...');
    if (!tokenRefreshPromise) {
      tokenRefreshPromise = refreshAuthToken();
      try {
        await tokenRefreshPromise;
        lastTokenRefresh = now;
      } finally {
        tokenRefreshPromise = null;
      }
    } else {
      await tokenRefreshPromise;
    }
  }
  
  return true;
};

const refreshAuthToken = async (): Promise<string> => {
  const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
  
  if (refreshError || !refreshData.session) {
    console.error('Session refresh failed:', refreshError?.message);
    throw new Error('Session refresh failed');
  }
  
  console.log('Session refreshed successfully');
  return refreshData.session.access_token;
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

// Request deduplication and caching
const makeApiRequest = async <T>(
  url: string, 
  options: RequestInit = {},
  cacheKey?: string,
  bypassCache = false
): Promise<T> => {
  // Generate cache key if not provided
  const key = cacheKey || `${options.method || 'GET'}:${url}:${JSON.stringify(options.body)}`;
  
  // Check cache first (for GET requests only)
  if (!bypassCache && (options.method || 'GET') === 'GET') {
    const cached = requestCache.get(key);
    if (cached) {
      const age = Date.now() - cached.timestamp;
      
      // Return fresh cache
      if (age < CACHE_TTL) {
        console.log(`Cache hit (fresh): ${key}`);
        return cached.data;
      }
      
      // Stale-while-revalidate: return stale data but trigger refresh
      if (age < STALE_WHILE_REVALIDATE_TTL) {
        console.log(`Cache hit (stale): ${key}, triggering background refresh`);
        // Trigger background refresh without awaiting
        makeApiRequest(url, options, cacheKey, true).then(freshData => {
          requestCache.set(key, { data: freshData, timestamp: Date.now() });
        }).catch(console.error);
        
        return cached.data;
      }
      
      // Remove expired cache
      requestCache.delete(key);
    }
  }
  
  // Check for pending request (deduplication)
  if (pendingRequests.has(key)) {
    console.log(`Request deduplication: ${key}`);
    return pendingRequests.get(key)!;
  }
  
  // Make the actual request
  const requestPromise = (async () => {
    try {
      await ensureAuthenticated();
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${API_URL}${url}`, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      });
      
      const data = await handleApiResponse(response);
      
      // Cache successful GET responses
      if ((options.method || 'GET') === 'GET' && !bypassCache) {
        requestCache.set(key, { data, timestamp: Date.now() });
        
        // Clean up old cache entries periodically
        if (requestCache.size > 100) {
          const now = Date.now();
          for (const [cacheKey, entry] of requestCache.entries()) {
            if (now - entry.timestamp > STALE_WHILE_REVALIDATE_TTL) {
              requestCache.delete(cacheKey);
            }
          }
        }
      }
      
      return data;
    } finally {
      pendingRequests.delete(key);
    }
  })();
  
  pendingRequests.set(key, requestPromise);
  return requestPromise;
};

// Dashboard API
export const dashboardApi = {
  async getInventoryDashboard(search?: string, page: number = 1, limit: number = 50) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    const cacheKey = `inventory-dashboard:${params.toString()}`;
    return makeApiRequest(`/dashboard/inventory?${params}`, { method: 'GET' }, cacheKey);
  },

  async getSalesAnalytics(period: number = 7) {
    const cacheKey = `sales-analytics:${period}`;
    return makeApiRequest(`/dashboard/analytics/sales?period=${period}`, { method: 'GET' }, cacheKey);
  },

  async getSales(period: number = 7, productId?: string, page: number = 1, limit: number = 50) {
    const params = new URLSearchParams();
    params.append('period', period.toString());
    if (productId) params.append('product_id', productId);
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    const cacheKey = `sales:${params.toString()}`;
    return makeApiRequest(`/dashboard/sales?${params}`, { method: 'GET' }, cacheKey);
  }
};

// Legacy functions - update to use new request method
export const createProduct = async (productData: any) => {
  return makeApiRequest('/inventory', {
    method: 'POST',
    body: JSON.stringify(productData),
  });
};

export const updateProduct = async (productId: string, productData: any) => {
  // Invalidate related cache entries
  requestCache.clear(); // Simple cache invalidation - can be more granular
  
  return makeApiRequest(`/inventory/${productId}`, {
    method: 'PUT',
    body: JSON.stringify(productData),
  });
};

export const deleteProduct = async (productId: string) => {
  // Invalidate related cache entries
  requestCache.clear();
  
  return makeApiRequest(`/inventory/${productId}`, {
    method: 'DELETE',
  });
};

export const getProducts = async (search?: string, page: number = 1, limit: number = 50) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  params.append('page', page.toString());
  params.append('limit', limit.toString());
  
  const cacheKey = `products:${params.toString()}`;
  return makeApiRequest(`/inventory?${params}`, { method: 'GET' }, cacheKey);
};

export const getAlerts = async () => {
  const cacheKey = 'alerts';
  return makeApiRequest('/alerts', { method: 'GET' }, cacheKey);
};

// Prefetch function for critical data
export const prefetchDashboardData = async () => {
  const prefetchPromises = [
    dashboardApi.getInventoryDashboard('', 1, 10), // Prefetch first page
    dashboardApi.getSalesAnalytics(7), // Prefetch weekly analytics
  ];
  
  // Execute prefetch in background without blocking
  Promise.allSettled(prefetchPromises).then(results => {
    console.log('Prefetch completed:', results.filter(r => r.status === 'fulfilled').length + ' successful');
  });
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