"use client"

import * as React from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { productsApi, suppliersApi } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

const formSchema = z.object({
  sku: z.string().min(2, {
    message: "SKU must be at least 2 characters.",
  }).regex(/^[a-zA-Z0-9-_]+$/, {
    message: "SKU must contain only letters, numbers, hyphens, and underscores."
  }),
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  supplier_id: z.string({
    required_error: "Please select a supplier.",
  }),
  cost: z.string().refine(val => !isNaN(parseFloat(val)), {
    message: "Cost must be a number.",
  }),
  on_hand: z.string().refine(val => !isNaN(parseInt(val)), {
    message: "Quantity must be a number.",
  }),
  reorder_point: z.string().refine(val => !isNaN(parseInt(val)), {
    message: "Reorder point must be a number.",
  }),
  safety_stock: z.string().refine(val => !val || !isNaN(parseInt(val)), {
    message: "Safety stock must be a number.",
  }).optional().or(z.literal('')),
  lead_time_days: z.string().refine(val => !val || !isNaN(parseInt(val)), {
    message: "Lead time must be a number.",
  }).optional().or(z.literal(''))
})

export interface ProductFormValues {
  id?: string  // UUID from backend
  sku: string
  name: string
  supplier_id: string
  cost: number
  on_hand: number
  reorder_point: number
  safety_stock?: number | null
  lead_time_days?: number | null
}

interface ProductFormProps {
  initialData?: ProductFormValues
  onSuccess: () => void
  onCancel: () => void
  onSubmitStart?: () => void
  disabled?: boolean
}

export function ProductForm({ 
  initialData, 
  onSuccess, 
  onCancel, 
  onSubmitStart,
  disabled = false 
}: ProductFormProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = React.useState(false)
  const [suppliers, setSuppliers] = React.useState<Array<{ id: string, name: string }>>([])
  const [isFetchingSuppliers, setIsFetchingSuppliers] = React.useState(true)
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      sku: initialData?.sku || "",
      name: initialData?.name || "",
      supplier_id: initialData?.supplier_id || "",
      cost: initialData?.cost ? String(initialData.cost) : "",
      on_hand: initialData?.on_hand ? String(initialData.on_hand) : "0",
      reorder_point: initialData?.reorder_point ? String(initialData.reorder_point) : "5",
      safety_stock: initialData?.safety_stock ? String(initialData.safety_stock) : "",
      lead_time_days: initialData?.lead_time_days ? String(initialData.lead_time_days) : "",
    },
  })

  // Fetch suppliers for the dropdown
  React.useEffect(() => {
    const getSuppliers = async () => {
      try {
        setIsFetchingSuppliers(true)
        const suppliersData = await suppliersApi.list()
        
        // Format suppliers for dropdown
        setSuppliers(
          suppliersData.map((supplier: any) => ({
            id: supplier.id,
            name: supplier.name
          }))
        )
      } catch (error) {
        console.error("Error fetching suppliers:", error)
        toast({
          title: "Error",
          description: "Failed to load suppliers. Please try again.",
          variant: "destructive",
        })
      } finally {
        setIsFetchingSuppliers(false)
      }
    }

    getSuppliers()
  }, [toast])

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      setIsLoading(true)
      if (onSubmitStart) onSubmitStart();
      
      // Convert string values to numbers
      const data = {
        ...values,
        cost: parseFloat(values.cost),
        on_hand: parseInt(values.on_hand),
        reorder_point: parseInt(values.reorder_point),
        safety_stock: values.safety_stock ? parseInt(values.safety_stock) : null,
        lead_time_days: values.lead_time_days ? parseInt(values.lead_time_days) : null,
      }
      
      if (initialData) {
        // Update existing product - ensure we have a valid UUID
        // The backend expects a UUID, not the SKU
        if (!(initialData as any).id) {
          throw new Error("Cannot update product: Missing product ID (UUID)");
        }
        const productId = (initialData as any).id;
        console.log(`Updating product with ID: ${productId}`);
        
        await productsApi.update(productId, data)
        toast({
          title: "Product updated",
          description: "The product has been updated successfully.",
        })
      } else {
        // Create new product - make sure SKU isn't a UUID format
        if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(values.sku)) {
          throw new Error("SKU cannot be in UUID format. Please use an alphanumeric code (e.g., RO-TOY).");
        }
        
        await productsApi.create(data)
        toast({
          title: "Product added",
          description: "The product has been added successfully.",
        })
      }
      
      onSuccess()
    } catch (error) {
      console.error("Product form error:", error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "An error occurred while saving the product.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="sku"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center">
                SKU <span className="text-destructive ml-1">*</span>
              </FormLabel>
              <FormControl>
                <Input placeholder="Product SKU (e.g., RO-TOY)" {...field} disabled={!!initialData || disabled} />
              </FormControl>
              <FormDescription>
                Unique identifier for the product (alphanumeric code, no spaces)
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center">
                Name <span className="text-destructive ml-1">*</span>
              </FormLabel>
              <FormControl>
                <Input placeholder="Product name" {...field} disabled={disabled} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="supplier_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center">
                Supplier <span className="text-destructive ml-1">*</span>
              </FormLabel>
              <Select 
                onValueChange={field.onChange} 
                defaultValue={field.value}
                disabled={isFetchingSuppliers || disabled}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a supplier" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {suppliers.map((supplier) => (
                    <SelectItem key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="cost"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center">
                Cost <span className="text-destructive ml-1">*</span>
              </FormLabel>
              <FormControl>
                <Input type="number" step="0.01" placeholder="0.00" {...field} disabled={disabled} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="on_hand"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center">
                Current Stock <span className="text-destructive ml-1">*</span>
              </FormLabel>
              <FormControl>
                <Input type="number" placeholder="0" {...field} disabled={disabled} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="reorder_point"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="flex items-center">
                Reorder Point <span className="text-destructive ml-1">*</span>
              </FormLabel>
              <FormControl>
                <Input type="number" placeholder="5" {...field} disabled={disabled} />
              </FormControl>
              <FormDescription>
                Minimum stock level before reordering
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="safety_stock"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Safety Stock</FormLabel>
              <FormControl>
                <Input type="number" placeholder="Optional" {...field} disabled={disabled} />
              </FormControl>
              <FormDescription>
                Buffer stock to prevent stockouts
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="lead_time_days"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Lead Time (days)</FormLabel>
              <FormControl>
                <Input type="number" placeholder="Optional" {...field} disabled={disabled} />
              </FormControl>
              <FormDescription>
                Average time for delivery in days
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel} type="button" disabled={isLoading || disabled}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading || disabled}>
            {isLoading ? "Saving..." : initialData ? "Update Product" : "Add Product"}
          </Button>
        </div>
      </form>
    </Form>
  )
} 