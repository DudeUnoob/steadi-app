import { create } from 'zustand'
import { supabase } from '../lib/supabase'

// Define types for connector data
interface ConnectorConfig {
  access_token?: string;
  refresh_token?: string;
  shop_domain?: string;
  account_id?: string;
  [key: string]: any;
}

interface Connector {
  id: string;
  provider: 'SHOPIFY' | 'SQUARE' | 'LIGHTSPEED' | 'CSV';
  status: 'PENDING' | 'ACTIVE' | 'ERROR';
  created_by: string;
  last_sync?: string;
  expires_at?: string;
  config?: ConnectorConfig;
}

interface ConnectorSync {
  connector_id: string;
  provider: string;
  status: string;
  items_synced: number;
  items_updated: number;
  items_created: number;
  sync_started_at: string;
  sync_completed_at?: string;
  errors: string[];
}

interface ConnectorTestResponse {
  provider: string;
  status: string;
  connection_valid: boolean;
  test_data?: any;
  error_message?: string;
}

interface CSVUploadResponse {
  imported_items: number;
  updated_items: number;
  created_items: number;
  errors: string[];
  warnings: string[];
}

interface OAuthInitRequest {
  oauth_code: string;
  shop_domain?: string;
  state?: string;
}

interface OAuthInitResponse {
  connector_id: string;
  provider: string;
  status: string;
  message: string;
}

interface ConnectorState {
  connectors: Connector[];
  isLoading: boolean;
  isSyncing: boolean;
  isUploading: boolean;
  error: string | null;
  syncResult: ConnectorSync | null;
  testResult: ConnectorTestResponse | null;
  uploadResult: CSVUploadResponse | null;
  
  // Actions
  fetchConnectors: () => Promise<void>;
  createConnector: (provider: string, config: ConnectorConfig) => Promise<void>;
  updateConnector: (id: string, config: ConnectorConfig) => Promise<void>;
  deleteConnector: (id: string) => Promise<void>;
  syncConnector: (id: string) => Promise<void>;
  testConnector: (id: string) => Promise<void>;
  uploadCSV: (file: File, mapping: any) => Promise<void>;
  getOAuthUrls: () => Promise<any>;
  initializeOAuth: (provider: string, data: OAuthInitRequest) => Promise<OAuthInitResponse>;
  resetError: () => void;
  resetResults: () => void;
}

// API functions
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjaWViY2hwZGp4ZnVtZW9hZnd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NDc2NTMsImV4cCI6MjA2MjMyMzY1M30.7hihI8t5_z7YFX_Yp9R4FgJYUvSFEOYix73Un-tWA0Y';

const getAuthHeaders = async () => {
  try {
    // Get Supabase session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session || !session.access_token) {
      throw new Error('No authenticated session available');
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
    
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${tokenData.access_token}`,
      'apikey': SUPABASE_ANON_KEY,
    };
  } catch (error) {
    console.error('Auth header retrieval error:', error);
    throw new Error('Authentication failed');
  }
};

const connectorApi = {
  async getConnectors(): Promise<Connector[]> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/`, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch connectors');
    }
    
    return response.json();
  },

  async createConnector(provider: string, config: ConnectorConfig): Promise<Connector> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ provider, config }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create connector');
    }
    
    return response.json();
  },

  async updateConnector(id: string, config: ConnectorConfig): Promise<Connector> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/${id}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ config }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update connector');
    }
    
    return response.json();
  },

  async deleteConnector(id: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/${id}`, {
      method: 'DELETE',
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete connector');
    }
  },

  async syncConnector(id: string): Promise<ConnectorSync> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/${id}/sync`, {
      method: 'POST',
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to sync connector');
    }
    
    return response.json();
  },

  async testConnector(id: string): Promise<ConnectorTestResponse> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/${id}/test`, {
      method: 'POST',
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to test connector');
    }
    
    return response.json();
  },

  async uploadCSV(file: File, mapping: any): Promise<CSVUploadResponse> {
    // Get auth headers using Supabase authentication
    const authHeaders = await getAuthHeaders();
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sku_column', mapping.sku_column);
    formData.append('name_column', mapping.name_column);
    formData.append('on_hand_column', mapping.on_hand_column);
    
    if (mapping.cost_column) {
      formData.append('cost_column', mapping.cost_column);
    }
    if (mapping.supplier_name_column) {
      formData.append('supplier_name_column', mapping.supplier_name_column);
    }
    if (mapping.variant_column) {
      formData.append('variant_column', mapping.variant_column);
    }
    
    const response = await fetch(`${API_URL}/connectors/csv/upload`, {
      method: 'POST',
      headers: {
        'Authorization': authHeaders.Authorization || '',
        'apikey': authHeaders.apikey || '',
      },
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload CSV');
    }
    
    return response.json();
  },

  async getOAuthUrls(): Promise<any> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/oauth/urls`, {
      headers,
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch OAuth URLs');
    }
    
    return response.json();
  },

  async initializeOAuth(provider: string, data: OAuthInitRequest): Promise<OAuthInitResponse> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/connectors/oauth/${provider.toLowerCase()}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to initialize OAuth');
    }
    
    return response.json();
  },
};

export const useConnectorStore = create<ConnectorState>((set, get) => ({
  connectors: [],
  isLoading: false,
  isSyncing: false,
  isUploading: false,
  error: null,
  syncResult: null,
  testResult: null,
  uploadResult: null,

  fetchConnectors: async () => {
    try {
      set({ isLoading: true, error: null });
      const connectors = await connectorApi.getConnectors();
      set({ connectors });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch connectors' });
    } finally {
      set({ isLoading: false });
    }
  },

  createConnector: async (provider: string, config: ConnectorConfig) => {
    try {
      set({ isLoading: true, error: null });
      const newConnector = await connectorApi.createConnector(provider, config);
      set(state => ({ 
        connectors: [...state.connectors, newConnector] 
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create connector' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  updateConnector: async (id: string, config: ConnectorConfig) => {
    try {
      set({ isLoading: true, error: null });
      const updatedConnector = await connectorApi.updateConnector(id, config);
      set(state => ({
        connectors: state.connectors.map(c => 
          c.id === id ? updatedConnector : c
        )
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update connector' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  deleteConnector: async (id: string) => {
    try {
      set({ isLoading: true, error: null });
      await connectorApi.deleteConnector(id);
      set(state => ({
        connectors: state.connectors.filter(c => c.id !== id)
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to delete connector' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  syncConnector: async (id: string) => {
    try {
      set({ isSyncing: true, error: null, syncResult: null });
      const result = await connectorApi.syncConnector(id);
      set({ syncResult: result });
      
      // Update connector status
      set(state => ({
        connectors: state.connectors.map(c => 
          c.id === id ? { ...c, status: result.status as any, last_sync: result.sync_completed_at } : c
        )
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to sync connector' });
    } finally {
      set({ isSyncing: false });
    }
  },

  testConnector: async (id: string) => {
    try {
      set({ isLoading: true, error: null, testResult: null });
      const result = await connectorApi.testConnector(id);
      set({ testResult: result });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to test connector' });
    } finally {
      set({ isLoading: false });
    }
  },

  uploadCSV: async (file: File, mapping: any) => {
    try {
      set({ isUploading: true, error: null, uploadResult: null });
      const result = await connectorApi.uploadCSV(file, mapping);
      set({ uploadResult: result });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to upload CSV' });
      throw error;
    } finally {
      set({ isUploading: false });
    }
  },

  getOAuthUrls: async () => {
    try {
      return await connectorApi.getOAuthUrls();
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch OAuth URLs' });
      throw error;
    }
  },

  initializeOAuth: async (provider: string, data: OAuthInitRequest) => {
    try {
      set({ isLoading: true, error: null });
      const result = await connectorApi.initializeOAuth(provider, data);
      
      // Refresh connectors list to include the new one
      await get().fetchConnectors();
      
      return result;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to initialize OAuth' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  resetError: () => set({ error: null }),
  resetResults: () => set({ syncResult: null, testResult: null, uploadResult: null }),
}))