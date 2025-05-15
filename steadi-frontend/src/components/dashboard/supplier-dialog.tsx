"use client"

import * as React from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { SupplierForm } from "./supplier-form"
import type { SupplierFormValues } from "./supplier-form"
import { Loader2 } from "lucide-react"

interface SupplierDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialData?: SupplierFormValues & { id?: string }
  onSuccess: () => void
}

export function SupplierDialog({ 
  open, 
  onOpenChange, 
  initialData, 
  onSuccess 
}: SupplierDialogProps) {
  const [isLoading, setIsLoading] = React.useState(false);
  
  // Reset loading state when dialog closes
  React.useEffect(() => {
    if (!open) {
      setIsLoading(false);
    }
  }, [open]);
  
  const handleSuccess = () => {
    setIsLoading(false);
    onSuccess();
    onOpenChange(false);
  };
  
  const handleCancel = () => {
    if (!isLoading) {
      onOpenChange(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={handleCancel}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{initialData ? "Edit Supplier" : "Add Supplier"}</DialogTitle>
          <DialogDescription>
            {initialData 
              ? "Update the supplier information below" 
              : "Fill out the form below to add a new supplier"}
          </DialogDescription>
        </DialogHeader>
        
        {isLoading && (
          <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-50 rounded-lg">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}
        
        <SupplierForm 
          initialData={initialData} 
          onSuccess={handleSuccess}
          onCancel={handleCancel}
          onSubmitStart={() => setIsLoading(true)}
        />
      </DialogContent>
    </Dialog>
  )
} 