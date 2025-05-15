"use client"

import { useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Overview } from "@/components/dashboard/overview"
import { SalesTable } from "@/components/dashboard/sales-table"
import { SuppliersTable } from "@/components/dashboard/suppliers-table"
import { ProductsTable } from "@/components/dashboard/products-table"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Button } from "@/components/ui/button"
import { Download, FileText, Users, Package, BarChart3, Loader2 } from "lucide-react"
import { DateRangePicker } from "@/components/dashboard/date-range-picker"
import { useToast } from "@/components/ui/use-toast"
// Import Zustand store
import { useDashboardStore } from "@/stores/dashboardStore"
import { dashboardApi } from "@/lib/api"
import type { DateRange } from "react-day-picker"

// Define types for the analytics data
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

export default function Dashboard() {
  const { toast } = useToast();

  // Use the Zustand store
  const dashboard = useDashboardStore();
  
  const { 
    salesAnalytics, 
    inventoryData, 
    isLoading, 
    error, 
    dateRange, 
    setDateRange,
    fetchDashboardData,
    resetError
  } = dashboard;

  useEffect(() => {
    // This will fetch data on component mount
    const initDashboard = async () => {
      try {
        // Use the store's fetch method
        await fetchDashboardData();
      } catch (error) {
        console.error("Error initializing dashboard:", error);
        toast({
          title: "Error",
          description: "Failed to load dashboard data. Please try again later.",
          variant: "destructive",
        });
      }
    };

    initDashboard();
  }, [fetchDashboardData, toast]);

  const handleDateRangeChange = (range: DateRange | undefined) => {
    if (range) {
      // This will trigger the API call automatically through the store
      setDateRange(range);
    }
  };

  const handleExport = async () => {
    try {
      toast({
        title: "Export initiated",
        description: "Your data is being prepared for download.",
      });
      
      // Here we would implement the actual export functionality
      // This could be a separate API endpoint or a client-side generation
    } catch (error) {
      toast({
        title: "Export failed",
        description: "There was a problem exporting your data.",
        variant: "destructive",
      });
    }
  };

  // Display loading state
  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col">
        <DashboardHeader />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <p className="text-lg">Loading dashboard data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Display error state
  if (error) {
    return (
      <div className="flex min-h-screen flex-col">
        <DashboardHeader />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md p-6 rounded-lg bg-destructive/10 border border-destructive/20">
            <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Dashboard</h2>
            <p className="mb-4">{error}</p>
            <Button 
              variant="outline" 
              onClick={() => {
                resetError();
                fetchDashboardData();
              }}
            >
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Calculate metrics from analytics data
  const totalRevenue = salesAnalytics?.top_sellers?.reduce((sum: number, seller: any) => sum + seller.revenue, 0) || 0;
  const revenueChange = salesAnalytics?.turnover_rate ? (salesAnalytics.turnover_rate * 100).toFixed(1) : "0.0";
  const activeSuppliers = inventoryData?.items?.filter((item: any) => item.badge !== "RED")?.length || 0;
  const totalProducts = inventoryData?.total || 0;
  const activeOrders = salesAnalytics?.active_orders || 0;

  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex-1">
        <DashboardShell>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
              <p className="text-muted-foreground">Monitor your business performance and make data-driven decisions.</p>
            </div>
            <div className="flex items-center gap-2">
              <DateRangePicker dateRange={dateRange} setDateRange={handleDateRangeChange} />
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </div>
          </div>
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="suppliers" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Suppliers
              </TabsTrigger>
              <TabsTrigger value="products" className="flex items-center gap-2">
                <Package className="h-4 w-4" />
                Products
              </TabsTrigger>
              <TabsTrigger value="sales" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Sales
              </TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-steadi-red"
                    >
                      <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">${totalRevenue.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">{revenueChange}% from last month</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Suppliers</CardTitle>
                    <Users className="h-4 w-4 text-steadi-pink" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">+{activeSuppliers}</div>
                    <p className="text-xs text-muted-foreground">+12% from last month</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Products</CardTitle>
                    <Package className="h-4 w-4 text-steadi-purple" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{totalProducts}</div>
                    <p className="text-xs text-muted-foreground">+{inventoryData?.items?.length || 0} active items</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Orders</CardTitle>
                    <FileText className="h-4 w-4 text-steadi-blue" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{activeOrders}</div>
                    <p className="text-xs text-muted-foreground">+5% from last month</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4">
                  <CardHeader>
                    <CardTitle>Overview</CardTitle>
                  </CardHeader>
                  <CardContent className="pl-2">
                    <Overview salesData={salesAnalytics?.monthly_sales} />
                  </CardContent>
                </Card>
                <Card className="col-span-3">
                  <CardHeader>
                    <CardTitle>Top Selling Products</CardTitle>
                    <CardDescription>
                      Your top performing products this month
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {salesAnalytics?.top_sellers?.map((seller, index) => (
                        <div className="flex items-center" key={index}>
                          <div className="w-[46px] h-[46px] rounded-md bg-primary/10 flex items-center justify-center mr-4">
                            <Package className="h-5 w-5 text-primary" />
                          </div>
                          <div className="space-y-1 flex-1">
                            <p className="text-sm font-medium leading-none">
                              {seller.name}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {seller.category || "General"}
                            </p>
                          </div>
                          <div className="font-medium">
                            ${seller.revenue.toLocaleString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="suppliers">
              <SuppliersTable />
            </TabsContent>
            <TabsContent value="products">
              <ProductsTable />
            </TabsContent>
            <TabsContent value="sales">
              <SalesTable />
            </TabsContent>
          </Tabs>
        </DashboardShell>
      </div>
    </div>
  );
}

// Fallback data in case API is unavailable
const topProducts = [
  {
    name: "Smart Inventory Manager",
    category: "Software",
    revenue: 45600,
  },
  {
    name: "Supply Chain Optimizer",
    category: "Software",
    revenue: 32400,
  },
  {
    name: "AI Sales Assistant",
    category: "Service",
    revenue: 28900,
  },
  {
    name: "Customer Insights Pro",
    category: "Analytics",
    revenue: 24500,
  },
]
