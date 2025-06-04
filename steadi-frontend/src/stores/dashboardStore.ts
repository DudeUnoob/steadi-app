import type { DateRange } from "react-day-picker"
import { create } from 'zustand'
import { dashboardApi, prefetchDashboardData } from "@/lib/api"

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

// Add debounce utility
const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

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
  lastFetchTime: number
  isOnline: boolean
  // Actions
  setDateRange: (range: DateRange) => void
  fetchDashboardData: () => Promise<void>
  fetchSalesData: (productId?: string, page?: number, limit?: number) => Promise<void>
  retryFetch: () => Promise<void>
  resetError: () => void
  prefetchData: () => void
  setOnlineStatus: (status: boolean) => void
}

export const useDashboardStore = create<DashboardState>((set, get) => {
  // Debounced date range handler
  const debouncedDateRangeUpdate = debounce(async (range: DateRange) => {
    const { from, to } = range;
    
    if (from && to) {
      const days = Math.round((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24));
      set({ period: days || 30 });
    }
    
    // Fetch data in parallel
    const { fetchDashboardData, fetchSalesData } = get();
    await Promise.allSettled([
      fetchDashboardData(),
      fetchSalesData()
    ]);
  }, 300); // 300ms debounce

  return {
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
    lastFetchTime: 0,
    isOnline: true,

    setOnlineStatus: (status: boolean) => {
      set({ isOnline: status });
      
      // Refetch data when coming back online
      if (status && !get().isLoading) {
        const { lastFetchTime } = get();
        const now = Date.now();
        
        // Refetch if last fetch was more than 5 minutes ago
        if (now - lastFetchTime > 5 * 60 * 1000) {
          get().fetchDashboardData();
        }
      }
    },

    setDateRange: (range: DateRange) => {
      set({ dateRange: range });
      debouncedDateRangeUpdate(range);
    },

    prefetchData: () => {
      // Only prefetch if we're online and not currently loading
      if (get().isOnline && !get().isLoading) {
        prefetchDashboardData();
      }
    },

    fetchDashboardData: async () => {
      const { period, isOnline } = get();
      
      if (!isOnline) {
        console.log('Offline mode: skipping data fetch');
        return;
      }
      
      try {
        set({ isLoading: true, error: null, lastFetchTime: Date.now() });
        
        // Fetch inventory and analytics in parallel for better performance
        const [inventoryResult, analyticsResult] = await Promise.allSettled([
          dashboardApi.getInventoryDashboard(),
          dashboardApi.getSalesAnalytics(period)
        ]);
        
        // Handle inventory result
        if (inventoryResult.status === 'fulfilled') {
          set({ inventoryData: inventoryResult.value as InventoryData });
        } else {
          console.error("Error fetching inventory data:", inventoryResult.reason);
        }
        
        // Handle analytics result
        if (analyticsResult.status === 'fulfilled') {
          set({ salesAnalytics: analyticsResult.value as SalesAnalytics });
        } else {
          console.error("Error fetching sales analytics:", analyticsResult.reason);
        }
        
        // Set error only if both failed
        if (inventoryResult.status === 'rejected' && analyticsResult.status === 'rejected') {
          set({ 
            error: `Failed to load dashboard data. Please check your connection and try again.`
          });
        } else {
          // Reset retry count on partial or full success
          set({ retryCount: 0 });
        }
        
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
        set({ 
          error: error instanceof Error ? error.message : "Failed to load dashboard data. Please try again later.",
        });
      } finally {
        set({ isLoading: false });
      }
    },
    
    fetchSalesData: async (productId?: string, page: number = 1, limit: number = 50) => {
      const { period, isOnline } = get();
      
      if (!isOnline) {
        console.log('Offline mode: skipping sales data fetch');
        return;
      }
      
      try {
        set({ isSalesLoading: true, salesError: null });
        
        const salesData = await dashboardApi.getSales(period, productId, page, limit);
        set({ salesData: salesData as SalesData });
        
      } catch (error) {
        console.error("Error fetching sales data:", error);
        set({ 
          salesError: error instanceof Error ? error.message : "Failed to load sales data. Please try again later.",
        });
      } finally {
        set({ isSalesLoading: false });
      }
    },

    retryFetch: async () => {
      const { retryCount, isOnline } = get();
      
      if (!isOnline) {
        console.log('Cannot retry while offline');
        return;
      }
      
      // Increment retry count
      set({ retryCount: retryCount + 1 });
      
      // Implement exponential backoff
      const delay = Math.min(1000 * (2 ** retryCount), 30000); // Max 30 seconds
      
      console.log(`Retrying fetch attempt ${retryCount + 1} after ${delay}ms delay`);
      
      // Wait for the backoff period
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Try fetching again with parallel requests
      await Promise.allSettled([
        get().fetchDashboardData(),
        get().fetchSalesData()
      ]);
    },

    resetError: () => {
      set({ error: null, salesError: null, retryCount: 0 });
    },
  };
});

// Set up online/offline event listeners
if (typeof window !== 'undefined') {
  const updateOnlineStatus = () => {
    useDashboardStore.getState().setOnlineStatus(navigator.onLine);
  };
  
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  
  // Initial status
  updateOnlineStatus();
} 