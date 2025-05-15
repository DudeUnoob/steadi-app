import type { DateRange } from "react-day-picker"
import { create } from 'zustand'
import { dashboardApi } from "@/lib/api"

// Define types for analytics data
interface SalesAnalytics {
  top_sellers: Array<{
    id?: string;
    name: string;
    category?: string;
    revenue: number;
  }>;
  turnover_rate: number;
  monthly_sales: Array<{ month: string; revenue: number }>;
  active_orders: number;
}

interface InventoryData {
  items: Array<{
    sku: string;
    name: string;
    on_hand: number;
    reorder_point: number;
    badge?: string;
    color: string;
    sales_trend: number[];
    days_of_stock: number;
  }>;
  total: number;
  page: number;
  limit: number;
  pages: number;
}

interface SaleItem {
  id: string;
  product_id: string;
  sku: string;
  name: string;
  quantity: number;
  sale_date: string;
  revenue: number;
}

interface DailyTotal {
  date: string;
  revenue: number;
  quantity: number;
}

interface MonthlyTotal {
  month: string;
  revenue: number;
}

interface SalesData {
  items: SaleItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  daily_totals: DailyTotal[];
  monthly_sales: MonthlyTotal[];
  period_days: number;
}

interface DashboardState {
  salesAnalytics: SalesAnalytics | null
  inventoryData: InventoryData | null
  salesData: SalesData | null
  isLoading: boolean
  isSalesLoading: boolean
  error: string | null
  salesError: string | null
  dateRange: DateRange
  period: number
  retryCount: number
  // Actions
  setDateRange: (range: DateRange) => void
  fetchDashboardData: () => Promise<void>
  fetchSalesData: (productId?: string, page?: number, limit?: number) => Promise<void>
  retryFetch: () => Promise<void>
  resetError: () => void
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  salesAnalytics: null,
  inventoryData: null,
  salesData: null,
  isLoading: false,
  isSalesLoading: false,
  error: null,
  salesError: null,
  dateRange: {
    from: new Date(new Date().setMonth(new Date().getMonth() - 1)),
    to: new Date(),
  },
  period: 30,
  retryCount: 0,

  setDateRange: (range: DateRange) => {
    set({ dateRange: range })
    const { from, to } = range
    
    if (from && to) {
      const days = Math.round((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24))
      set({ period: days || 30 }) // Use 30 as fallback if calculation fails
    }
    
    // Trigger data fetch when date range changes
    const { fetchDashboardData, fetchSalesData } = get()
    fetchDashboardData()
    fetchSalesData()
  },

  fetchDashboardData: async () => {
    const { period } = get()
    
    try {
      set({ isLoading: true, error: null })
      
      // First try to fetch inventory data - the more critical component
      try {
        const inventory = await dashboardApi.getInventoryDashboard()
        set({ inventoryData: inventory })
      } catch (inventoryError) {
        console.error("Error fetching inventory data:", inventoryError)
        // Continue with sales data even if inventory fails
        set({ 
          error: `Failed to load inventory data: ${
            inventoryError instanceof Error ? inventoryError.message : "Unknown error"
          }`
        })
      }
      
      // Then try to fetch sales analytics data
      try {
        const analytics = await dashboardApi.getSalesAnalytics(period)
        set({ salesAnalytics: analytics })
      } catch (salesError) {
        console.error("Error fetching sales analytics:", salesError)
        // Set error only if we don't already have one from inventory
        if (!get().error) {
          set({ 
            error: `Failed to load sales analytics: ${
              salesError instanceof Error ? salesError.message : "Unknown error"
            }`
          })
        }
      }
      
      // Reset retry count on success
      if (get().inventoryData || get().salesAnalytics) {
        set({ retryCount: 0 })
      }
      
    } catch (error) {
      console.error("Error fetching dashboard data:", error)
      set({ 
        error: error instanceof Error ? error.message : "Failed to load dashboard data. Please try again later.",
      })
    } finally {
      set({ isLoading: false })
    }
  },
  
  fetchSalesData: async (productId?: string, page: number = 1, limit: number = 50) => {
    const { period } = get()
    
    try {
      set({ isSalesLoading: true, salesError: null })
      
      const salesData = await dashboardApi.getSales(period, productId, page, limit)
      set({ salesData })
      
    } catch (error) {
      console.error("Error fetching sales data:", error)
      set({ 
        salesError: error instanceof Error ? error.message : "Failed to load sales data. Please try again later.",
      })
    } finally {
      set({ isSalesLoading: false })
    }
  },

  retryFetch: async () => {
    const { retryCount } = get()
    
    // Increment retry count
    set({ retryCount: retryCount + 1 })
    
    // Implement exponential backoff
    const delay = Math.min(1000 * (2 ** retryCount), 30000) // Max 30 seconds
    
    console.log(`Retrying fetch attempt ${retryCount + 1} after ${delay}ms delay`)
    
    // Wait for the backoff period
    await new Promise(resolve => setTimeout(resolve, delay))
    
    // Try fetching again
    return get().fetchDashboardData()
  },

  resetError: () => set({ error: null, salesError: null })
})) 