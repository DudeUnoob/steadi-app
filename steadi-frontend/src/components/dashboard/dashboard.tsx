"use client"

import { useEffect, useRef } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Overview } from "@/components/dashboard/overview"
import { SalesTable } from "@/components/dashboard/sales-table"
import { SuppliersTable } from "@/components/dashboard/suppliers-table"
import { ProductsTable } from "@/components/dashboard/products-table"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Button } from "@/components/ui/button"
import { Download, FileText, Users, Package, BarChart3, Loader2, Wifi, WifiOff } from "lucide-react"
import { DateRangePicker } from "@/components/dashboard/date-range-picker"
import { useToast } from "@/components/ui/use-toast"
// Import Zustand store
import { useDashboardStore } from "@/stores/dashboardStore"
import type { DateRange } from "react-day-picker"
// Import performance hooks
import { usePerformanceMonitor, useIntersectionObserver } from "@/hooks/use-performance"

export default function Dashboard() {
  const { toast } = useToast();
  const dashboardRef = useRef<HTMLDivElement>(null);
  
  // Performance monitoring
  const metrics = usePerformanceMonitor('Dashboard');
  const isVisible = useIntersectionObserver(dashboardRef);

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
    resetError,
    prefetchData,
    isOnline
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

  // Prefetch data when component becomes visible
  useEffect(() => {
    if (isVisible && isOnline) {
      prefetchData();
    }
  }, [isVisible, isOnline, prefetchData]);

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

  const handleRetry = () => {
    resetError();
    fetchDashboardData();
  };

  // Display loading state with better UX
  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col" ref={dashboardRef}>
        <DashboardHeader />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <div className="text-center">
              <p className="text-lg font-medium">Loading dashboard data...</p>
              <p className="text-sm text-muted-foreground">
                This may take a few moments for large datasets
              </p>
            </div>
            {!isOnline && (
              <div className="flex items-center space-x-2 text-orange-600">
                <WifiOff className="h-4 w-4" />
                <span className="text-sm">You're currently offline</span>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Display error state with retry functionality
  if (error) {
    return (
      <div className="flex min-h-screen flex-col" ref={dashboardRef}>
        <DashboardHeader />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md p-6 rounded-lg bg-destructive/10 border border-destructive/20">
            <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Dashboard</h2>
            <p className="mb-4 text-sm text-muted-foreground">{error}</p>
            <div className="space-y-2">
              <Button onClick={handleRetry}>
                Try Again
              </Button>
              {!isOnline && (
                <div className="flex items-center justify-center space-x-2 text-orange-600">
                  <WifiOff className="h-4 w-4" />
                  <span className="text-sm">Check your internet connection</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Calculate metrics from analytics data with fallbacks
  const totalRevenue = salesAnalytics?.top_sellers?.reduce((sum: number, seller: any) => sum + (seller.revenue || 0), 0) || 0;
  const revenueChange = salesAnalytics?.turnover_rate ? (salesAnalytics.turnover_rate * 100).toFixed(1) : "0.0";
  const activeSuppliers = inventoryData?.items?.filter((item: any) => item.badge !== "RED")?.length || 0;
  const totalProducts = inventoryData?.total || 0;
  const activeOrders = salesAnalytics?.active_orders || 0;

  return (
    <div className="flex min-h-screen flex-col" ref={dashboardRef}>
      <DashboardHeader />
      <div className="flex-1">
        <DashboardShell>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
              <p className="text-muted-foreground">Monitor your business performance and make data-driven decisions.</p>
            </div>
            <div className="flex items-center gap-2">
              {!isOnline && (
                <div className="flex items-center space-x-1 text-orange-600 text-sm">
                  <WifiOff className="h-4 w-4" />
                  <span>Offline</span>
                </div>
              )}
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
                    <p className="text-xs text-muted-foreground">+5% from last month</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Orders</CardTitle>
                    <FileText className="h-4 w-4 text-steadi-blue" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{activeOrders}</div>
                    <p className="text-xs text-muted-foreground">+2% from last hour</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4">
                  <CardHeader>
                    <CardTitle>Revenue Overview</CardTitle>
                  </CardHeader>
                  <CardContent className="pl-2">
                    <Overview data={salesAnalytics?.monthly_sales || []} />
                  </CardContent>
                </Card>
                <Card className="col-span-3">
                  <CardHeader>
                    <CardTitle>Recent Sales</CardTitle>
                    <CardDescription>
                      You made {salesAnalytics?.top_sellers?.length || 0} sales this period.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <SalesTable data={salesAnalytics?.top_sellers || []} />
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="suppliers" className="space-y-4">
              <SuppliersTable />
            </TabsContent>
            <TabsContent value="products" className="space-y-4">
              <ProductsTable />
            </TabsContent>
            <TabsContent value="sales" className="space-y-4">
              <SalesTable data={salesAnalytics?.top_sellers || []} />
            </TabsContent>
          </Tabs>
        </DashboardShell>
      </div>
    </div>
  )
}
