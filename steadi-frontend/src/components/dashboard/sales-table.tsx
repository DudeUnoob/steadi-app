"use client"

import * as React from "react"
import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type VisibilityState,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { salesApi } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  BarChart,
  Bar,
  Legend
} from 'recharts'
import { useDashboardStore } from "@/stores/dashboardStore"
import { formatCurrency } from "@/lib/utils"

export type Sale = {
  id: string
  product: string
  product_id: string
  quantity: number
  sale_date: string
  total: number
  notes?: string
}

// Fallback data
const fallbackData: Sale[] = [
  {
    id: "SALE001",
    product: "Smart Inventory Manager",
    product_id: "PROD001",
    quantity: 2,
    sale_date: "2023-05-15",
    total: 2599.98,
    notes: "Online purchase"
  },
  // ... other fallback data
]

interface SalesTableProps {
  productId?: string
  data?: Array<{
    id?: string
    name: string
    category?: string
    revenue: number
  }>
}

export function SalesTable({ productId, data }: SalesTableProps) {
  const { toast } = useToast()
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})
  const [sales, setSales] = React.useState<Sale[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  
  // State for dialogs
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)
  const [selectedSale, setSelectedSale] = React.useState<Sale | null>(null)

  const { salesData, isSalesLoading, salesError, fetchSalesData } = useDashboardStore()
  const [currentPage, setCurrentPage] = React.useState(1)
  const [itemsPerPage] = React.useState(10)
  
  const fetchSales = React.useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await salesApi.list()
      
      // Transform the API response to match our Sale type
      const formattedSales = response.map((sale: any) => ({
        id: sale.id,
        product: sale.product_name || 'Unknown Product',
        product_id: sale.product_id,
        quantity: sale.quantity,
        sale_date: new Date(sale.sale_date).toISOString().split('T')[0],
        total: sale.amount || (sale.quantity * sale.cost) || 0,
        notes: sale.notes,
      }))
      
      setSales(formattedSales)
    } catch (error) {
      console.error("Error fetching sales:", error)
      toast({
        title: "Error",
        description: "Failed to load sales. Showing fallback data.",
        variant: "destructive",
      })
      setSales(fallbackData)
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  React.useEffect(() => {
    // If data prop is provided, use it directly (for summary tables)
    if (data && data.length > 0) {
      const transformedData = data.map((item, index) => ({
        id: item.id || `summary-${index}`,
        product: item.name,
        product_id: item.id || `prod-${index}`,
        quantity: 1, // Default quantity for summary
        sale_date: new Date().toISOString().split('T')[0], // Today's date
        total: item.revenue,
        notes: item.category || ""
      }))
      setSales(transformedData)
      setIsLoading(false)
      return
    }
    
    // Otherwise, fetch sales normally
    fetchSales()
  }, [fetchSales, data])

  React.useEffect(() => {
    fetchSalesData(productId, currentPage, itemsPerPage)
  }, [fetchSalesData, productId, currentPage, itemsPerPage])
  
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  }

  // Handle delete sale
  const handleDeleteSale = async () => {
    if (!selectedSale) return
    
    try {
      // Log the ID being used
      console.log(`Attempting to delete sale with ID: ${selectedSale.id}`);
      
      // Ensure we're using the UUID, not a display ID
      const saleUuid = selectedSale.id;
      
      await salesApi.delete(saleUuid)
      toast({
        title: "Sale deleted",
        description: "The sale has been deleted successfully.",
      })
      fetchSales()
      // Also refresh the dashboard data if available
      if (fetchSalesData) {
        fetchSalesData(productId, currentPage, itemsPerPage);
      }
    } catch (error) {
      console.error("Error deleting sale:", error)
      
      // Provide more specific error messages
      let errorMessage = "An error occurred while deleting the sale.";
      
      if (error instanceof Error) {
        errorMessage = error.message;
        
        // Handle specific error cases
        if (errorMessage.includes("not found")) {
          errorMessage = "Sale not found or you don't have permission to delete it.";
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setDeleteDialogOpen(false)
      setSelectedSale(null)
    }
  }

  const columns: ColumnDef<Sale>[] = [
    {
      accessorKey: "id",
      header: "ID",
      cell: ({ row }) => <div className="font-medium">{row.getValue("id")}</div>,
    },
    {
      accessorKey: "product",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Product
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="font-medium">{row.getValue("product")}</div>,
    },
    {
      accessorKey: "quantity",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Quantity
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="text-center">{row.getValue("quantity")}</div>,
    },
    {
      accessorKey: "sale_date",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Date
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => {
        const date = new Date(row.getValue("sale_date"))
        return <div>{date.toLocaleDateString()}</div>
      },
    },
    {
      accessorKey: "total",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Total
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => {
        const amount = Number.parseFloat(row.getValue("total"))
        const formatted = new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
        }).format(amount)

        return <div className="text-right font-medium">{formatted}</div>
      },
    },
    {
      accessorKey: "notes",
      header: "Notes",
      cell: ({ row }) => <div className="truncate max-w-[200px]">{row.getValue("notes") || "-"}</div>,
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const sale = row.original

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-background">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(sale.id)}>
                Copy sale ID
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={() => {
                  setSelectedSale(sale)
                  setDeleteDialogOpen(true)
                }}
                className="text-destructive focus:text-destructive"
              >
                Delete sale
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ]

  // Table configuration is defined but not used in this version of the component
  useReactTable({
    data: sales,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading sales...</span>
      </div>
    )
  }

  if (isSalesLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }
  
  if (salesError) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Sales Data</CardTitle>
          <CardDescription>Error loading sales data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-4 text-red-500">
            {salesError}
          </div>
        </CardContent>
      </Card>
    )
  }
  
  if (!salesData || !salesData.items || salesData.items.length === 0) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Sales Data</CardTitle>
          <CardDescription>No sales data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-4 text-gray-500">
            No sales records found for the selected period.
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Sales Analytics Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Daily Sales</CardTitle>
            <CardDescription>Revenue by day for the selected period</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={salesData.daily_totals}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => formatCurrency(Number(value))}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="revenue" 
                    stroke="#8884d8" 
                    name="Revenue" 
                    activeDot={{ r: 8 }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Monthly Revenue</CardTitle>
            <CardDescription>Revenue by month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={salesData.monthly_sales}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => formatCurrency(Number(value))}
                  />
                  <Bar 
                    dataKey="revenue" 
                    fill="#82ca9d" 
                    name="Revenue" 
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Sales Table */}
      <Card>
        <CardHeader>
          <CardTitle>Sales Records</CardTitle>
          <CardDescription>
            {productId 
              ? "Sales records for selected product"
              : "Recent sales records"
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="text-right">Revenue</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {salesData.items.map((sale) => (
                  <TableRow key={sale.id}>
                    <TableCell>{formatDate(sale.sale_date)}</TableCell>
                    <TableCell className="font-medium">{sale.name}</TableCell>
                    <TableCell>{sale.sku}</TableCell>
                    <TableCell className="text-right">{sale.quantity}</TableCell>
                    <TableCell className="text-right">{formatCurrency(sale.revenue)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          
          {/* Pagination */}
          {salesData.pages > 1 && (
            <div className="flex items-center justify-center space-x-2 py-4">
              <Pagination>
                <PaginationContent>
                  {currentPage > 1 && (
                    <PaginationItem>
                      <PaginationPrevious 
                        onClick={() => handlePageChange(currentPage - 1)}
                      />
                    </PaginationItem>
                  )}
                  
                  {[...Array(Math.min(5, salesData.pages))].map((_, i) => {
                    const page = i + 1
                    return (
                      <PaginationItem key={page}>
                        <PaginationLink
                          onClick={() => handlePageChange(page)}
                          isActive={currentPage === page}
                        >
                          {page}
                        </PaginationLink>
                      </PaginationItem>
                    )
                  })}
                  
                  {currentPage < salesData.pages && (
                    <PaginationItem>
                      <PaginationNext 
                        onClick={() => handlePageChange(currentPage + 1)}
                      />
                    </PaginationItem>
                  )}
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the sale record. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteSale} className="bg-destructive">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
