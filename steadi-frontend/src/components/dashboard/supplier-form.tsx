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
import { Textarea } from "@/components/ui/textarea"
import { suppliersApi } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

const formSchema = z.object({
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  contact_email: z.string().email({
    message: "Please enter a valid email address.",
  }).optional().or(z.literal('')),
  phone: z.string().optional().or(z.literal('')),
  lead_time_days: z.string().refine(val => !val || !isNaN(parseInt(val)), {
    message: "Lead time must be a number.",
  }).optional().or(z.literal('')),
  notes: z.string().optional().or(z.literal('')),
})

export interface SupplierFormValues {
  name: string
  contact_email?: string
  phone?: string
  lead_time_days?: number | null
  notes?: string
}

interface SupplierFormProps {
  initialData?: SupplierFormValues & { id?: string }
  onSuccess: () => void
  onCancel: () => void
  onSubmitStart?: () => void
}

export function SupplierForm({ 
  initialData, 
  onSuccess, 
  onCancel, 
  onSubmitStart 
}: SupplierFormProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = React.useState(false)
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: initialData?.name || "",
      contact_email: initialData?.contact_email || "",
      phone: initialData?.phone || "",
      lead_time_days: initialData?.lead_time_days ? String(initialData.lead_time_days) : "",
      notes: initialData?.notes || "",
    },
  })

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      setIsLoading(true)
      if (onSubmitStart) onSubmitStart();
      
      // Convert lead_time_days to number, using default of 7 if empty
      const data = {
        ...values,
        lead_time_days: values.lead_time_days && values.lead_time_days.trim() !== '' 
          ? parseInt(values.lead_time_days) 
          : 7, // Default lead time of 7 days
      }
      
      if (initialData?.id) {
        // Update existing supplier
        console.log(`Updating supplier with ID: ${initialData.id}`);
        await suppliersApi.update(initialData.id, data)
        toast({
          title: "Supplier updated",
          description: "The supplier has been updated successfully.",
        })
      } else {
        // Create new supplier
        console.log(`Creating new supplier: ${values.name}`);
        await suppliersApi.create(data)
        toast({
          title: "Supplier added",
          description: "The supplier has been added successfully.",
        })
      }
      
      onSuccess()
    } catch (error) {
      console.error("Supplier form error:", error)
      
      // More detailed error handling
      let errorMessage = "An error occurred while saving the supplier."
      
      if (error instanceof Error) {
        errorMessage = error.message
        
        // Handle specific error types
        if (errorMessage.includes("already exists")) {
          errorMessage = "A supplier with this name already exists."
        } else if (errorMessage.includes("not found")) {
          errorMessage = "The supplier could not be found or you don't have permission to modify it."
        }
      }
      
      toast({
        title: "Error",
        description: errorMessage,
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
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Supplier name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="contact_email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input placeholder="contact@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="phone"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Phone</FormLabel>
              <FormControl>
                <Input placeholder="Phone number" {...field} />
              </FormControl>
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
                <Input type="number" placeholder="7" {...field} />
              </FormControl>
              <FormDescription>
                Average time for delivery in days. Default is 7 days if not specified.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes</FormLabel>
              <FormControl>
                <Textarea placeholder="Additional information about the supplier" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel} type="button" disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Saving..." : initialData ? "Update Supplier" : "Add Supplier"}
          </Button>
        </div>
      </form>
    </Form>
  )
} 