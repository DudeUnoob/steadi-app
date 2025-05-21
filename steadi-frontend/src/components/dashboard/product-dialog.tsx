"use client"

import * as React from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ProductForm } from "./product-form"
import type { ProductFormValues } from "./product-form"
import { Loader2 } from "lucide-react"

interface ProductDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: ProductFormValues
  onSuccess: () => void
  isLoading?: boolean
}

export function ProductDialog({ 
  open, 
  onOpenChange, 
  initialData, 
  onSuccess,
  isLoading = false
}: ProductDialogProps) {
  const [localLoading, setLocalLoading] = React.useState(false);
  
  // Reset local loading state when dialog closes
  React.useEffect(() => {
    if (!open) {
      setLocalLoading(false);
    }
  }, [open]);
  
  const handleSuccess = () => {
    setLocalLoading(false);
    onSuccess();
    onOpenChange(false);
  };
  
  const handleCancel = () => {
    if (!localLoading && !isLoading) {
      onOpenChange(false);
    }
  };

  // Combine external and local loading states
  const isFormLoading = isLoading || localLoading;
  
  // Format the initial data for the form, ensuring the id field is included
  const formattedInitialData = initialData ? {
    ...initialData,
    // Ensure id field is included if present
    id: initialData.id || undefined
  } : undefined;
  
  return (
    <Dialog open={open} onOpenChange={handleCancel}>
      <DialogContent className="sm:max-w-[550px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {initialData 
              ? `Edit Product (${initialData.sku})` 
              : "Add New Product"
            }
          </DialogTitle>
          <DialogDescription>
            {initialData 
              ? `Update product details for ${initialData.name}` 
              : "Fill out the form below to add a new product. Required fields are marked with *"
            }
          </DialogDescription>
        </DialogHeader>
        
        {isFormLoading && (
          <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-50 rounded-lg">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}
        
        <ProductForm 
          initialData={formattedInitialData} 
          onSuccess={handleSuccess}
          onCancel={handleCancel}
          onSubmitStart={() => setLocalLoading(true)}
          disabled={isFormLoading}
        />
      </DialogContent>
    </Dialog>
  )
} 