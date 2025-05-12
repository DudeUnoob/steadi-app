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
import { ArrowUpDown, ChevronDown, MoreHorizontal } from "lucide-react"

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

export type Supplier = {
  id: string
  name: string
  email: string
  status: "active" | "pending" | "inactive"
  products: number
  performance: "excellent" | "good" | "average" | "poor"
  lastDelivery: string
}

const data: Supplier[] = [
  {
    id: "SUP001",
    name: "TechPro Solutions",
    email: "contact@techpro.com",
    status: "active",
    products: 24,
    performance: "excellent",
    lastDelivery: "2023-04-23",
  },
  {
    id: "SUP002",
    name: "Global Logistics Inc.",
    email: "orders@globallogistics.com",
    status: "active",
    products: 18,
    performance: "good",
    lastDelivery: "2023-04-18",
  },
  {
    id: "SUP003",
    name: "Innovative Materials",
    email: "sales@innovativematerials.com",
    status: "inactive",
    products: 12,
    performance: "poor",
    lastDelivery: "2023-03-05",
  },
  {
    id: "SUP004",
    name: "Quality Components Ltd.",
    email: "info@qualitycomponents.com",
    status: "active",
    products: 32,
    performance: "excellent",
    lastDelivery: "2023-04-21",
  },
  {
    id: "SUP005",
    name: "Precision Manufacturing",
    email: "orders@precisionmfg.com",
    status: "pending",
    products: 8,
    performance: "average",
    lastDelivery: "2023-04-10",
  },
  {
    id: "SUP006",
    name: "EcoFriendly Packaging",
    email: "sales@ecofriendly.com",
    status: "active",
    products: 15,
    performance: "good",
    lastDelivery: "2023-04-15",
  },
  {
    id: "SUP007",
    name: "Digital Solutions Group",
    email: "support@digitalsolutions.com",
    status: "active",
    products: 21,
    performance: "excellent",
    lastDelivery: "2023-04-22",
  },
]

export function SuppliersTable() {
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})

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
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(supplier.id)}>
                Copy supplier ID
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>View supplier details</DropdownMenuItem>
              <DropdownMenuItem>View products</DropdownMenuItem>
              <DropdownMenuItem>Update supplier</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ]

  const table = useReactTable({
    data,
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

  return (
    <div className="w-full">
      <div className="flex items-center py-4">
        <Input
          placeholder="Filter suppliers..."
          value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
          onChange={(event) => table.getColumn("name")?.setFilterValue(event.target.value)}
          className="max-w-sm"
        />
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
                    onCheckedChange={(value) => column.toggleVisibility(!!value)}
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                )
              })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="rounded-md border border-[#2a2a30] overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/30">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="border-b-[#2a2a30] hover:bg-muted/20">
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
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
                  className="border-b-[#2a2a30] hover:bg-muted/20"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-end space-x-2 py-4">
        <div className="flex-1 text-sm text-muted-foreground">
          {table.getFilteredSelectedRowModel().rows.length} of {table.getFilteredRowModel().rows.length} row(s)
          selected.
        </div>
        <div className="space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
