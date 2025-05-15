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
import { suppliersApi } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"
import { SupplierDialog } from "./supplier-dialog"
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

export type Supplier = {
  id: string
  name: string
  email: string
  status: "active" | "pending" | "inactive"
  products: number
  performance: "excellent" | "good" | "average" | "poor"
  lastDelivery: string
}

// Fallback data
const fallbackData: Supplier[] = [
  {
    id: "SUP001",
    name: "TechPro Solutions",
    email: "contact@techpro.com",
    status: "active",
    products: 24,
    performance: "excellent",
    lastDelivery: "2023-04-23",
  },
  // ... other fallback data
]

export function SuppliersTable() {
  const { toast } = useToast()
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})
  const [suppliers, setSuppliers] = React.useState<Supplier[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  
  // State for dialogs
  const [addDialogOpen, setAddDialogOpen] = React.useState(false)
  const [editDialogOpen, setEditDialogOpen] = React.useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)
  const [selectedSupplier, setSelectedSupplier] = React.useState<Supplier | null>(null)
  const [viewDetailsDialogOpen, setViewDetailsDialogOpen] = React.useState(false)

  const fetchSuppliers = React.useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await suppliersApi.list()
      
      // Transform the API response to match our Supplier type
      const formattedSuppliers = response.map((supplier: any) => ({
        id: supplier.id,
        name: supplier.name,
        email: supplier.contact_email || 'N/A',
        status: supplier.is_active ? 'active' : 'inactive',
        products: supplier.product_count || 0,
        performance: supplier.performance || 'average',
        lastDelivery: supplier.last_delivery_date || new Date().toISOString().split('T')[0],
      }))
      
      setSuppliers(formattedSuppliers)
    } catch (error) {
      console.error("Error fetching suppliers:", error)
      toast({
        title: "Error",
        description: "Failed to load suppliers. Showing fallback data.",
        variant: "destructive",
      })
      setSuppliers(fallbackData)
    } finally {
      setIsLoading(false)
    }
  }, [toast])

  React.useEffect(() => {
    fetchSuppliers()
  }, [fetchSuppliers])

  // Handle delete supplier
  const handleDeleteSupplier = async () => {
    if (!selectedSupplier) return
    
    try {
      // Log the ID being used
      console.log(`Attempting to delete supplier with ID: ${selectedSupplier.id}`);
      
      // Ensure we're using the UUID, not a display ID
      const supplierUuid = selectedSupplier.id;
      
      await suppliersApi.delete(supplierUuid)
      toast({
        title: "Supplier deleted",
        description: "The supplier has been deleted successfully.",
      })
      fetchSuppliers()
    } catch (error) {
      console.error("Error deleting supplier:", error)
      
      // Provide more specific error messages
      let errorMessage = "An error occurred while deleting the supplier.";
      
      if (error instanceof Error) {
        errorMessage = error.message;
        
        // Handle specific error cases
        if (errorMessage.includes("associated")) {
          errorMessage = "Cannot delete supplier with associated products.";
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setDeleteDialogOpen(false)
      setSelectedSupplier(null)
    }
  }

  const columns: ColumnDef<Supplier>[] = [
    {
      accessorKey: "id",
      header: "ID",
      cell: ({ row }) => <div className="font-medium">{row.getValue("id")}</div>,
    },
    {
      accessorKey: "name",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Supplier
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="font-medium">{row.getValue("name")}</div>,
    },
    {
      accessorKey: "email",
      header: "Email",
      cell: ({ row }) => <div className="lowercase">{row.getValue("email")}</div>,
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const status = row.getValue("status") as string
        return (
          <Badge
            variant={status === "active" ? "default" : status === "pending" ? "outline" : "secondary"}
            className={
              status === "active"
                ? "bg-green-500 hover:bg-green-600"
                : status === "pending"
                  ? "border-amber-500 text-amber-500 hover:bg-amber-50"
                  : "bg-gray-500 hover:bg-gray-600"
            }
          >
            {status}
          </Badge>
        )
      },
    },
    {
      accessorKey: "products",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Products
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="text-center">{row.getValue("products")}</div>,
    },
    {
      accessorKey: "performance",
      header: "Performance",
      cell: ({ row }) => {
        const performance = row.getValue("performance") as string
        return (
          <Badge
            variant="outline"
            className={
              performance === "excellent"
                ? "border-green-500 text-green-500"
                : performance === "good"
                  ? "border-blue-500 text-blue-500"
                  : performance === "average"
                    ? "border-amber-500 text-amber-500"
                    : "border-red-500 text-red-500"
            }
          >
            {performance}
          </Badge>
        )
      },
    },
    {
      accessorKey: "lastDelivery",
      header: "Last Delivery",
      cell: ({ row }) => {
        const date = new Date(row.getValue("lastDelivery"))
        return <div>{date.toLocaleDateString()}</div>
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const supplier = row.original

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
              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(supplier.id)}>
                Copy supplier ID
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => {
                setSelectedSupplier(supplier)
                setViewDetailsDialogOpen(true)
              }}>
                View supplier details
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => {
                setSelectedSupplier(supplier)
                setEditDialogOpen(true)
              }}>
                Update supplier
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => {
                  setSelectedSupplier(supplier)
                  setDeleteDialogOpen(true)
                }}
                className="text-destructive focus:text-destructive"
              >
                Delete supplier
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ]

  const table = useReactTable({
    data: suppliers,
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
        <span className="ml-2">Loading suppliers...</span>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between py-4">
        <Input
          placeholder="Filter suppliers..."
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
            <Plus className="mr-2 h-4 w-4" /> Add Supplier
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
                  No suppliers found.
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

      {/* Add/Edit Supplier Dialog */}
      <SupplierDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSuccess={fetchSuppliers}
      />
      
      {/* Edit Supplier Dialog */}
      {selectedSupplier && (
        <SupplierDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          initialData={{
            id: selectedSupplier.id,
            name: selectedSupplier.name,
            contact_email: selectedSupplier.email !== 'N/A' ? selectedSupplier.email : undefined,
            phone: undefined,
            lead_time_days: undefined,
            notes: undefined,
          }}
          onSuccess={fetchSuppliers}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the supplier {selectedSupplier?.name}. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteSupplier} className="bg-destructive">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
