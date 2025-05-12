"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Overview } from "@/components/overview"
import { SalesTable } from "@/components/sales-table"
import { SuppliersTable } from "@/components/suppliers-table"
import { ProductsTable } from "@/components/products-table"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardShell } from "@/components/dashboard-shell"
import { Button } from "@/components/ui/button"
import { Download, FileText, Users, Package, BarChart3 } from "lucide-react"
import { DateRangePicker } from "@/components/date-range-picker"
export default function Dashboard() {
  const [dateRange, setDateRange] = useState<{ from: Date; to: Date }>({
    from: new Date(new Date().setMonth(new Date().getMonth() - 1)),
    to: new Date(),
  })

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
              <DateRangePicker dateRange={dateRange} setDateRange={setDateRange} />
              <Button variant="outline" size="sm">
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
                <Card className="futuristic-card border-0">
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
                    <div className="text-2xl font-bold">$45,231.89</div>
                    <p className="text-xs text-muted-foreground">+20.1% from last month</p>
                  </CardContent>
                </Card>
                <Card className="futuristic-card border-0">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Suppliers</CardTitle>
                    <Users className="h-4 w-4 text-steadi-pink" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">+24</div>
                    <p className="text-xs text-muted-foreground">+12% from last month</p>
                  </CardContent>
                </Card>
                <Card className="futuristic-card border-0">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Products</CardTitle>
                    <Package className="h-4 w-4 text-steadi-purple" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">+573</div>
                    <p className="text-xs text-muted-foreground">+54 since last month</p>
                  </CardContent>
                </Card>
                <Card className="futuristic-card border-0">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Orders</CardTitle>
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
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">+89</div>
                    <p className="text-xs text-muted-foreground">+14.2% from last month</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 futuristic-card border-0">
                  <CardHeader>
                    <CardTitle>Sales Overview</CardTitle>
                    <CardDescription>Monthly sales performance for the current year.</CardDescription>
                  </CardHeader>
                  <CardContent className="pl-2">
                    <Overview />
                  </CardContent>
                </Card>
                <Card className="col-span-3 futuristic-card border-0">
                  <CardHeader>
                    <CardTitle>Top Products</CardTitle>
                    <CardDescription>Best selling products by revenue.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {topProducts.map((product) => (
                        <div key={product.name} className="flex items-center">
                          <div className="w-[46px] h-[46px] rounded-md flex items-center justify-center bg-muted mr-4">
                            <Package className="h-5 w-5 text-steadi-pink" />
                          </div>
                          <div className="flex-1 space-y-1">
                            <p className="text-sm font-medium leading-none">{product.name}</p>
                            <p className="text-xs text-muted-foreground">{product.category}</p>
                          </div>
                          <div className="text-sm font-medium">${product.revenue.toLocaleString()}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="suppliers" className="space-y-4">
              <Card className="futuristic-card border-0">
                <CardHeader>
                  <CardTitle>Suppliers</CardTitle>
                  <CardDescription>Manage your suppliers and their performance.</CardDescription>
                </CardHeader>
                <CardContent>
                  <SuppliersTable />
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="products" className="space-y-4">
              <Card className="futuristic-card border-0">
                <CardHeader>
                  <CardTitle>Products</CardTitle>
                  <CardDescription>View and manage your product inventory.</CardDescription>
                </CardHeader>
                <CardContent>
                  <ProductsTable />
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="sales" className="space-y-4">
              <Card className="futuristic-card border-0">
                <CardHeader>
                  <CardTitle>Sales</CardTitle>
                  <CardDescription>Track your sales performance and order history.</CardDescription>
                </CardHeader>
                <CardContent>
                  <SalesTable />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </DashboardShell>
      </div>
    </div>
  )
}

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
