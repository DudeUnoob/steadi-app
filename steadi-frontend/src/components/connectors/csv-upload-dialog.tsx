"use client"

import { useState, useRef } from "react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { 
  Upload, 
  FileText, 
  Loader2, 
  CheckCircle, 
  AlertTriangle,
  X,
  Download
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useConnectorStore } from "@/stores/connectorStore"

interface CSVUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CSVUploadDialog({ open, onOpenChange }: CSVUploadDialogProps) {
  const { toast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [csvHeaders, setCsvHeaders] = useState<string[]>([])
  const [mapping, setMapping] = useState({    sku_column: "",    name_column: "",    on_hand_column: "",    cost_column: "none",    supplier_name_column: "none",    variant_column: "none"  })
  const [step, setStep] = useState<'upload' | 'mapping' | 'processing' | 'results'>('upload')

  const { uploadCSV, isUploading, uploadResult, resetResults } = useConnectorStore()

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile)
      parseCSVHeaders(selectedFile)
    } else {
      toast({
        title: "Invalid file",
        description: "Please select a valid CSV file",
        variant: "destructive",
      })
    }
  }

  const parseCSVHeaders = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const firstLine = text.split('\n')[0]
      const headers = firstLine.split(',').map(h => h.trim().replace(/"/g, ''))
      setCsvHeaders(headers)
      setStep('mapping')
    }
    reader.readAsText(file)
  }

  const handleMappingChange = (field: string, value: string) => {
    setMapping(prev => ({
      ...prev,
      [field]: value === "none" ? "" : value
    }))
  }

  const handleUpload = async () => {
    if (!file || !mapping.sku_column || !mapping.name_column || !mapping.on_hand_column) {
      toast({
        title: "Missing required fields",
        description: "Please map SKU, Name, and Quantity columns",
        variant: "destructive",
      })
      return
    }

    setStep('processing')
    
    try {
      await uploadCSV(file, mapping)
      setStep('results')
    } catch (error) {
      setStep('mapping')
    }
  }

  const handleClose = () => {
    setFile(null)
    setCsvHeaders([])
    setMapping({
      sku_column: "",
      name_column: "",
      on_hand_column: "",
      cost_column: "none",
      supplier_name_column: "none",
      variant_column: "none"
    })
    setStep('upload')
    resetResults()
    onOpenChange(false)
  }

  const downloadSampleCSV = () => {
    const sampleData = [
      ['SKU', 'Name', 'Quantity', 'Cost', 'Supplier', 'Variant'],
      ['PROD001', 'Sample Product 1', '10', '25.99', 'Supplier A', 'Red'],
      ['PROD002', 'Sample Product 2', '5', '15.50', 'Supplier B', 'Blue'],
      ['PROD003', 'Sample Product 3', '20', '8.75', 'Supplier A', '']
    ]
    
    const csvContent = sampleData.map(row => row.join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'sample-inventory.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const renderUploadStep = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div 
          className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 cursor-pointer hover:border-muted-foreground/50 transition-colors"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">Upload CSV File</h3>
          <p className="text-muted-foreground mb-4">
            Click to select a CSV file or drag and drop
          </p>
          <Button variant="outline">
            <FileText className="w-4 h-4 mr-2" />
            Select File
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">CSV Format Requirements</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p><strong>Required columns:</strong> SKU, Product Name, Quantity</p>
          <p><strong>Optional columns:</strong> Cost, Supplier, Variant</p>
          <p><strong>Format:</strong> Standard CSV with comma separators</p>
          <div className="flex items-center gap-2 mt-4">
            <Button variant="outline" size="sm" onClick={downloadSampleCSV}>
              <Download className="w-3 h-3 mr-1" />
              Download Sample
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderMappingStep = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Map CSV Columns</h3>
          <p className="text-muted-foreground">
            Map your CSV columns to the required fields
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setStep('upload')}>
          <X className="w-4 h-4 mr-1" />
          Change File
        </Button>
      </div>

      {file && (
        <Alert>
          <FileText className="h-4 w-4" />
          <AlertDescription>
            File: {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>SKU Column *</Label>
          <Select value={mapping.sku_column} onValueChange={(value) => handleMappingChange('sku_column', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select SKU column" />
            </SelectTrigger>
            <SelectContent>
              {csvHeaders.map(header => (
                <SelectItem key={header} value={header}>{header}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Product Name Column *</Label>
          <Select value={mapping.name_column} onValueChange={(value) => handleMappingChange('name_column', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select name column" />
            </SelectTrigger>
            <SelectContent>
              {csvHeaders.map(header => (
                <SelectItem key={header} value={header}>{header}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Quantity Column *</Label>
          <Select value={mapping.on_hand_column} onValueChange={(value) => handleMappingChange('on_hand_column', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select quantity column" />
            </SelectTrigger>
            <SelectContent>
              {csvHeaders.map(header => (
                <SelectItem key={header} value={header}>{header}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Cost Column (Optional)</Label>
          <Select value={mapping.cost_column} onValueChange={(value) => handleMappingChange('cost_column', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select cost column" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              {csvHeaders.map(header => (
                <SelectItem key={header} value={header}>{header}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Supplier Column (Optional)</Label>
          <Select value={mapping.supplier_name_column} onValueChange={(value) => handleMappingChange('supplier_name_column', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select supplier column" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              {csvHeaders.map(header => (
                <SelectItem key={header} value={header}>{header}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Variant Column (Optional)</Label>
          <Select value={mapping.variant_column} onValueChange={(value) => handleMappingChange('variant_column', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select variant column" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              {csvHeaders.map(header => (
                <SelectItem key={header} value={header}>{header}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  )

  const renderProcessingStep = () => (
    <div className="space-y-6 text-center">
      <div className="flex flex-col items-center">
        <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
        <h3 className="text-lg font-semibold mb-2">Processing CSV File</h3>
        <p className="text-muted-foreground">
          Importing your inventory data...
        </p>
      </div>
      <Progress value={undefined} className="w-full" />
    </div>
  )

  const renderResultsStep = () => (
    <div className="space-y-6">
      <div className="text-center">
        <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
        <h3 className="text-lg font-semibold mb-2">Import Complete</h3>
      </div>

      {uploadResult && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-green-600">
                  {uploadResult.created_items}
                </div>
                <p className="text-sm text-muted-foreground">Items Created</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-blue-600">
                  {uploadResult.updated_items}
                </div>
                <p className="text-sm text-muted-foreground">Items Updated</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {uploadResult.imported_items}
                </div>
                <p className="text-sm text-muted-foreground">Total Processed</p>
              </CardContent>
            </Card>
          </div>

          {uploadResult.errors.length > 0 && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="font-semibold mb-2">Errors ({uploadResult.errors.length}):</div>
                <ul className="list-disc list-inside space-y-1">
                  {uploadResult.errors.slice(0, 5).map((error, index) => (
                    <li key={index} className="text-sm">{error}</li>
                  ))}
                  {uploadResult.errors.length > 5 && (
                    <li className="text-sm">... and {uploadResult.errors.length - 5} more</li>
                  )}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {uploadResult.warnings.length > 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="font-semibold mb-2">Warnings ({uploadResult.warnings.length}):</div>
                <ul className="list-disc list-inside space-y-1">
                  {uploadResult.warnings.slice(0, 3).map((warning, index) => (
                    <li key={index} className="text-sm">{warning}</li>
                  ))}
                  {uploadResult.warnings.length > 3 && (
                    <li className="text-sm">... and {uploadResult.warnings.length - 3} more</li>
                  )}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </div>
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Import Inventory from CSV
          </DialogTitle>
          <DialogDescription>
            Upload a CSV file to import or update your inventory data
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-[400px]">
          {step === 'upload' && renderUploadStep()}
          {step === 'mapping' && renderMappingStep()}
          {step === 'processing' && renderProcessingStep()}
          {step === 'results' && renderResultsStep()}
        </div>

        <DialogFooter>
          {step === 'upload' && (
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
          )}
          
          {step === 'mapping' && (
            <>
              <Button variant="outline" onClick={() => setStep('upload')}>
                Back
              </Button>
              <Button 
                onClick={handleUpload}
                disabled={!mapping.sku_column || !mapping.name_column || !mapping.on_hand_column || isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  "Import Data"
                )}
              </Button>
            </>
          )}
          
          {step === 'results' && (
            <Button onClick={handleClose}>
              Done
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 