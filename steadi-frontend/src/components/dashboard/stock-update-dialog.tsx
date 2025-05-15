"use client"

import * as React from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { productsApi } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

const formSchema = z.object({
  on_hand: z.string().refine(val => !isNaN(parseInt(val)), {
    message: "Stock must be a number.",
  }),
})

interface StockUpdateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  productId: string
  productName: string
  currentStock: number
  onSuccess: () => void
}

export function StockUpdateDialog({ 
  open, 
  onOpenChange, 
  productId, 
  productName,
  currentStock,
  onSuccess 
}: StockUpdateDialogProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = React.useState(false)
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      on_hand: String(currentStock),
    },
  })

  React.useEffect(() => {
    if (open) {
      // Reset form with current stock when dialog opens
      form.reset({
        on_hand: String(currentStock),
      })
    }
  }, [open, currentStock, form])

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      setIsLoading(true)
      
      // Validate productId is a valid UUID
      const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!productId || !uuidPattern.test(productId)) {
        throw new Error("Invalid product ID format. The system requires a UUID.");
      }
      
      // Log the action for debugging
      console.log(`Updating stock for product ID: ${productId} to ${values.on_hand}`);
      
      // Convert string values to numbers
      const data = {
        on_hand: parseInt(values.on_hand),
      }
      
      await productsApi.update(productId, data)
      toast({
        title: "Stock updated",
        description: "The product stock has been updated successfully.",
      })
      
      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error("Stock update error:", error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "An error occurred while updating the stock.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Update Stock</DialogTitle>
          <DialogDescription>
            Update the current stock quantity for {productName}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="on_hand"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Current Stock</FormLabel>
                  <FormControl>
                    <Input type="number" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)} type="button" disabled={isLoading}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Updating..." : "Update Stock"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 