import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper function to get auth headers
const getAuthHeaders = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session?.access_token}`,
  };
};

// Products API
export const productsApi = {
  list: async () => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/products`, { headers });
    if (!response.ok) throw new Error('Failed to fetch products');
    return response.json();
  },

  create: async (data: any) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/products`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create product');
    return response.json();
  },

  update: async (id: string, data: any) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/products/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update product');
    return response.json();
  },

  delete: async (id: string) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/products/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!response.ok) throw new Error('Failed to delete product');
    return response.json();
  },
};

// Suppliers API
export const suppliersApi = {
  list: async () => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/suppliers`, { headers });
    if (!response.ok) throw new Error('Failed to fetch suppliers');
    return response.json();
  },

  create: async (data: any) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/suppliers`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create supplier');
    return response.json();
  },

  update: async (id: string, data: any) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/suppliers/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update supplier');
    return response.json();
  },

  delete: async (id: string) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/suppliers/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!response.ok) throw new Error('Failed to delete supplier');
    return response.json();
  },
};

// Sales API
export const salesApi = {
  list: async () => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/sales`, { headers });
    if (!response.ok) throw new Error('Failed to fetch sales');
    return response.json();
  },

  create: async (data: any) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/sales`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create sale');
    return response.json();
  },

  update: async (id: string, data: any) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/sales/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update sale');
    return response.json();
  },

  delete: async (id: string) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/edit/sales/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!response.ok) throw new Error('Failed to delete sale');
    return response.json();
  },
}; 