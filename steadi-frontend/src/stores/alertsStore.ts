import { create } from 'zustand'

// Define types for alerts data
interface AlertItem {
  id: string
  sku: string
  name: string
  on_hand: number
  reorder_point: number
  safety_stock: number
  alert_level: 'RED' | 'YELLOW'
  supplier_name?: string
  supplier_contact?: string
  supplier_id?: string
  days_of_stock: number
  lead_time_days: number
  needs_immediate_action: boolean
  reorder_quantity: number
}

interface AlertCounts {
  red: number
  yellow: number
  normal: number
  total: number
}

interface Notification {
  id: string
  channel: 'EMAIL' | 'IN_APP' | 'SMS'
  payload: {
    type?: string
    message?: string
    product_id?: string
    product_name?: string
    sku?: string
    alert_level?: string
    [key: string]: any
  }
  sent_at: string
  read_at?: string
}

interface RateLimitStatus {
  requests_made: number
  requests_remaining: number
  limit: number
  window_seconds: number
  reset_time?: number
  is_limited: boolean
}

interface AlertSummary {
  alert_counts: AlertCounts
  unread_notifications: number
  rate_limit_status: RateLimitStatus
  recent_notifications: number
  needs_immediate_attention: boolean
  total_products_monitored: number
}

interface AlertsState {
  // Data
  alerts: AlertItem[]
  notifications: Notification[]
  alertCounts: AlertCounts | null
  alertSummary: AlertSummary | null
  rateLimitStatus: RateLimitStatus | null
  
  // Loading states
  isLoading: boolean
  isNotificationsLoading: boolean
  isSendingEmail: boolean
  
  // Error states
  error: string | null
  notificationsError: string | null
  emailError: string | null
  
  // Actions
  fetchAlerts: () => Promise<void>
  fetchNotifications: (includeRead?: boolean, limit?: number) => Promise<void>
  fetchAlertSummary: () => Promise<void>
  fetchRateLimitStatus: () => Promise<void>
  sendEmailAlerts: () => Promise<boolean>
  markNotificationRead: (notificationId: string) => Promise<boolean>
  markAllNotificationsRead: () => Promise<boolean>
  deleteNotification: (notificationId: string) => Promise<boolean>
  resetErrors: () => void
}

// API base URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Import the auth functions from the existing API
import { supabase } from '@/lib/supabase'

// Helper function to get auth headers (matching existing api.ts pattern)
const getAuthHeaders = async () => {
  try {
    // Get Supabase session
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session || !session.access_token) {
      throw new Error('No authenticated session available')
    }
    
    // Exchange Supabase token for backend token
    const exchangeResponse = await fetch(`${API_URL}/supabase-auth/token`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (!exchangeResponse.ok) {
      throw new Error('Failed to exchange token with backend')
    }
    
    const tokenData = await exchangeResponse.json()
    
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${tokenData.access_token}`,
      'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY || '',
    }
  } catch (error) {
    console.error('Auth header retrieval error:', error)
    throw new Error('Could not validate credentials')
  }
}

export const useAlertsStore = create<AlertsState>((set, get) => ({
  // Initial state
  alerts: [],
  notifications: [],
  alertCounts: null,
  alertSummary: null,
  rateLimitStatus: null,
  isLoading: false,
  isNotificationsLoading: false,
  isSendingEmail: false,
  error: null,
  notificationsError: null,
  emailError: null,

  fetchAlerts: async () => {
    try {
      set({ isLoading: true, error: null })
      
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/alerts/reorder`, {
        headers
      })
      
      if (!response.ok) {
        throw new Error(`Failed to fetch alerts: ${response.statusText}`)
      }
      
      const alerts = await response.json()
      set({ alerts, isLoading: false })
      
    } catch (error) {
      console.error('Error fetching alerts:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch alerts',
        isLoading: false 
      })
    }
  },

  fetchNotifications: async (includeRead = false, limit = 50) => {
    try {
      set({ isNotificationsLoading: true, notificationsError: null })
      
      const headers = await getAuthHeaders()
      const params = new URLSearchParams({
        include_read: includeRead.toString(),
        limit: limit.toString()
      })
      
      const response = await fetch(`${API_URL}/alerts/notifications?${params}`, {
        headers
      })
      
      if (!response.ok) {
        throw new Error(`Failed to fetch notifications: ${response.statusText}`)
      }
      
      const notifications = await response.json()
      set({ notifications, isNotificationsLoading: false })
      
    } catch (error) {
      console.error('Error fetching notifications:', error)
      set({ 
        notificationsError: error instanceof Error ? error.message : 'Failed to fetch notifications',
        isNotificationsLoading: false 
      })
    }
  },

  fetchAlertSummary: async () => {
    try {
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/alerts/summary`, {
        headers
      })
      
      if (!response.ok) {
        throw new Error(`Failed to fetch alert summary: ${response.statusText}`)
      }
      
      const alertSummary = await response.json()
      set({ 
        alertSummary,
        alertCounts: alertSummary.alert_counts,
        rateLimitStatus: alertSummary.rate_limit_status
      })
      
    } catch (error) {
      console.error('Error fetching alert summary:', error)
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch alert summary'
      })
    }
  },

  fetchRateLimitStatus: async () => {
    try {
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/alerts/rate-limit-status`, {
        headers
      })
      
      if (!response.ok) {
        throw new Error(`Failed to fetch rate limit status: ${response.statusText}`)
      }
      
      const rateLimitStatus = await response.json()
      set({ rateLimitStatus })
      
    } catch (error) {
      console.error('Error fetching rate limit status:', error)
    }
  },

  sendEmailAlerts: async () => {
    try {
      set({ isSendingEmail: true, emailError: null })
      
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/alerts/send-email`, {
        method: 'POST',
        headers
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to send email alerts: ${response.statusText}`)
      }
      
      const result = await response.json()
      
      // Refresh data after sending email
      await get().fetchAlertSummary()
      await get().fetchNotifications()
      
      set({ isSendingEmail: false })
      return true
      
    } catch (error) {
      console.error('Error sending email alerts:', error)
      set({ 
        emailError: error instanceof Error ? error.message : 'Failed to send email alerts',
        isSendingEmail: false 
      })
      return false
    }
  },

  markNotificationRead: async (notificationId: string) => {
    try {
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/alerts/notifications/${notificationId}/mark-read`, {
        method: 'POST',
        headers
      })
      
      if (!response.ok) {
        throw new Error(`Failed to mark notification as read: ${response.statusText}`)
      }
      
      // Update local state
      set(state => ({
        notifications: state.notifications.map(notif => 
          notif.id === notificationId 
            ? { ...notif, read_at: new Date().toISOString() }
            : notif
        )
      }))
      
      // Refresh summary to update unread count
      await get().fetchAlertSummary()
      
      return true
      
    } catch (error) {
      console.error('Error marking notification as read:', error)
      return false
    }
  },

  markAllNotificationsRead: async () => {
    try {
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/alerts/notifications/mark-all-read`, {
        method: 'POST',
        headers
      })
      
      if (!response.ok) {
        throw new Error(`Failed to mark all notifications as read: ${response.statusText}`)
      }
      
      // Update local state
      const now = new Date().toISOString()
      set(state => ({
        notifications: state.notifications.map(notif => ({ ...notif, read_at: now }))
      }))
      
      // Refresh summary
      await get().fetchAlertSummary()
      
      return true
      
    } catch (error) {
      console.error('Error marking all notifications as read:', error)
      return false
    }
  },

  deleteNotification: async (notificationId: string) => {
    try {
      const headers = await getAuthHeaders()
      const response = await fetch(`${API_URL}/alerts/notifications/${notificationId}`, {
        method: 'DELETE',
        headers
      })
      
      if (!response.ok) {
        throw new Error(`Failed to delete notification: ${response.statusText}`)
      }
      
      // Update local state
      set(state => ({
        notifications: state.notifications.filter(notif => notif.id !== notificationId)
      }))
      
      // Refresh summary
      await get().fetchAlertSummary()
      
      return true
      
    } catch (error) {
      console.error('Error deleting notification:', error)
      return false
    }
  },

  resetErrors: () => {
    set({ error: null, notificationsError: null, emailError: null })
  }
})) 