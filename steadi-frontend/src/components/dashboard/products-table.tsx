"use client"

import * as React from "react"
import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown, MoreHorizontal, Loader2, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { productsApi, dashboardApi, suppliersApi } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"
import { ProductDialog } from "./product-dialog"
import { StockUpdateDialog } from "./stock-update-dialog"
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

export type Product = {
  id: string        // This will hold the actual UUID from backend
  sku: string       // SKU for display
  name: string
  category: string
  cost: number
  stock: number
  status: "in-stock" | "low-stock" | "out-of-stock"
  supplier: string
  supplier_id?: string
  reorder_point?: number
  safety_stock?: number | null
  lead_time_days?: number | null
}

// Fallback data
const fallbackData: Product[] = [
  {
    id: "00000000-0000-0000-0000-000000000000", // Placeholder UUID
    sku: "PROD001",
    name: "Smart Inventory Manager",
    category: "Software",
    cost: 1299.99,
    stock: 50,
    status: "in-stock",
    supplier: "TechPro Solutions",
  },
  // ... other fallback data
]

export function ProductsTable() {
  const { toast } = useToast()
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})
  const [products, setProducts] = React.useState<Product[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  
  // State for dialogs
  const [addDialogOpen, setAddDialogOpen] = React.useState(false)
  const [editDialogOpen, setEditDialogOpen] = React.useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)
  const [selectedProduct, setSelectedProduct] = React.useState<Product | null>(null)
  const [updateStockDialogOpen, setUpdateStockDialogOpen] = React.useState(false)

  const fetchProducts = React.useCallback(async () => {
    try {
      setIsLoading(true)
      // Get detailed product data first to get the UUIDs
      const productsList = await productsApi.list()
      
      // Use the inventory dashboard endpoint to get product data with stock status
      const response = await dashboardApi.getInventoryDashboard() as { items: any[] }
      
      // Create a mapping from SKU to product ID (UUID)
      const productMap = productsList.reduce((map: {[key: string]: any}, product: any) => {
        map[product.sku] = product;
        return map;
      }, {});
      
      // Also create a supplier mapping to resolve supplier names
      const suppliersData = await suppliersApi.list();
      const supplierMap = suppliersData.reduce((map: {[key: string]: any}, supplier: any) => {
        map[supplier.id] = supplier.name;
        return map;
      }, {});
      
      // Transform the API response to match our Product type
      const formattedProducts = response.items.map((product: any) => {
        // Determine status based on stock level
        let status: "in-stock" | "low-stock" | "out-of-stock" = "in-stock"
        if (product.on_hand <= 0) {
          status = "out-of-stock"
        } else if (product.badge === "YELLOW" || product.badge === "RED") {
          status = "low-stock"
        }
        
        // Find detailed product info from the products map
        const detailedProduct = productMap[product.sku];
        
        // Ensure we have a valid UUID from the detailed product data
        // This is critical for API operations
        if (!detailedProduct?.id) {
          console.warn(`Missing UUID for product with SKU: ${product.sku}`);
        }
        
        // Get the supplier name from the supplier map if we have a supplier_id
        const supplierName = detailedProduct?.supplier_id ? 
          supplierMap[detailedProduct.supplier_id] || "Unknown" : 
          "Unknown";
        
        return {
          id: detailedProduct?.id || "00000000-0000-0000-0000-000000000000", // Use UUID from detailed data
          sku: product.sku,
          name: product.name,
          category: product.category || "General",
          cost: detailedProduct?.cost || 0, // Use cost from detailed product data, not dashboard data
          stock: product.on_hand,
          status,
          supplier: supplierName, // Use resolved supplier name
          supplier_id: detailedProduct?.supplier_id,
          reorder_point: detailedProduct?.reorder_point || product.reorder_point,
          safety_stock: detailedProduct?.safety_stock,
          lead_time_days: detailedProduct?.lead_time_days,
        }
      })
      
      setProducts(formattedProducts)
    } catch (error) {
      console.error("Error fetching products:", error)
      toast({
        title: "Error",
        description: "Failed to load products. Showing fallback data.",
        variant: "destructive",
      })
      setProducts(fallbackData)
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  React.useEffect(() => {
    fetchProducts()
  }, [fetchProducts])

  // Handle delete product
  const handleDeleteProduct = async () => {
    if (!selectedProduct) return
    
    try {
      // Validate that we have a valid UUID
      if (!selectedProduct.id || selectedProduct.id === "00000000-0000-0000-0000-000000000000") {
        throw new Error("Cannot delete product: Invalid product ID");
      }
      
      // Check if the ID looks like a UUID (basic validation)
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!uuidPattern.test(selectedProduct.id)) {
        throw new Error("Cannot delete product: ID is not a valid UUID format");
      }
      
      // Log the ID we're using to delete the product
      console.log(`Attempting to delete product with ID: ${selectedProduct.id}`);
      
      await productsApi.delete(selectedProduct.id)
      toast({
        title: "Product deleted",
        description: "The product has been deleted successfully.",
      })
      fetchProducts()
    } catch (error) {
      console.error("Error deleting product:", error)
      
      // Provide more specific error messages
      let errorMessage = "An error occurred while deleting the product.";
      
      if (error instanceof Error) {
        errorMessage = error.message;
        
        // Handle specific error cases
        if (errorMessage.includes("not found")) {
          errorMessage = "Product not found or you don't have permission to delete it.";
        } else if (errorMessage.includes("associated sales")) {
          errorMessage = "Cannot delete product with associated sales.";
        } else if (errorMessage.includes("422") || errorMessage.includes("Unprocessable Entity")) {
          errorMessage = "Invalid product ID format. The system requires a UUID.";
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setDeleteDialogOpen(false)
      setSelectedProduct(null)
    }
  }

  

  const columns: ColumnDef<Product>[] = [
    {
      accessorKey: "sku",
      header: "SKU",
      cell: ({ row }) => (
        <div className="font-medium" title={`ID: ${row.original.id}`}>
          {row.getValue("sku")}
        </div>
      ),
    },
    {
      accessorKey: "name",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Product
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="font-medium">{row.getValue("name")}</div>,
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => <div>{row.getValue("category")}</div>,
    },
    {
      accessorKey: "cost",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Cost
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => {
        const amount = Number.parseFloat(row.getValue("cost"))
        const formatted = new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
        }).format(amount)

        return <div className="text-right font-medium">{formatted}</div>
      },
    },
    {
      accessorKey: "stock",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Stock
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="text-center">{row.getValue("stock")}</div>,
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const status = row.getValue("status") as string
        return (
          <Badge
            variant={status === "in-stock" ? "default" : status === "low-stock" ? "outline" : "secondary"}
            className={
              status === "in-stock"
                ? "bg-green-500 hover:bg-green-600"
                : status === "low-stock"
                  ? "border-amber-500 text-amber-500 hover:bg-amber-50"
                  : "bg-red-500 hover:bg-red-600"
            }
          >
            {status}
          </Badge>
        )
      },
    },
    {
      accessorKey: "supplier",
      header: "Supplier",
      cell: ({ row }) => <div>{row.getValue("supplier")}</div>,
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const product = row.original

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
              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(product.id)}>
                Copy product ID
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => {
                setSelectedProduct(product)
                setEditDialogOpen(true)
              }}>
                Edit product
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => {
                setSelectedProduct(product)
                setUpdateStockDialogOpen(true)
              }}>
                Update stock
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => {
                  setSelectedProduct(product)
                  setDeleteDialogOpen(true)
                }}
                className="text-destructive focus:text-destructive"
              >
                Delete product
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ]

  const table = useReactTable({
    data: products,
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
        <span className="ml-2">Loading products...</span>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between py-4">
        <Input
          placeholder="Filter products..."
          value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn("name")?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="ml-auto">
                Columns <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {table
                .getAllColumns()
                .filter((column) => column.getCanHide())
                .map((column) => {
                  return (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className="capitalize"
                      checked={column.getIsVisible()}
                      onCheckedChange={(value) =>
                        column.toggleVisibility(!!value)
                      }
                    >
                      {column.id}
                    </DropdownMenuCheckboxItem>
                  )
                })}
            </DropdownMenuContent>
          </DropdownMenu>
          <Button onClick={() => setAddDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Add Product
          </Button>
        </div>
      </div>
      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No products found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between space-x-2 py-4">
        <div className="text-sm text-muted-foreground">
          {table.getFilteredSelectedRowModel().rows.length} of{" "}
          {table.getFilteredRowModel().rows.length} row(s) selected.
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </Button>
        </div>
      </div>

      {/* Add Product Dialog */}
      <ProductDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSuccess={fetchProducts}
      />
      
      {/* Edit Product Dialog */}
      {selectedProduct && (
        <ProductDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          initialData={{
            id: selectedProduct.id,
            sku: selectedProduct.sku,
            name: selectedProduct.name,
            supplier_id: selectedProduct.supplier_id || "",
            cost: selectedProduct.cost,
            on_hand: selectedProduct.stock,
            reorder_point: selectedProduct.reorder_point || 5,
            safety_stock: selectedProduct.safety_stock,
            lead_time_days: selectedProduct.lead_time_days,
          }}
          onSuccess={fetchProducts}
        />
      )}

      {/* Stock Update Dialog */}
      {selectedProduct && (
        <StockUpdateDialog
          open={updateStockDialogOpen}
          onOpenChange={setUpdateStockDialogOpen}
          productId={selectedProduct.id}
          productName={selectedProduct.name}
          currentStock={selectedProduct.stock}
          onSuccess={fetchProducts}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the product {selectedProduct?.name}. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteProduct} className="bg-destructive">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
