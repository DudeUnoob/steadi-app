"use client"

import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  TestTube, 
  CheckCircle, 
  XCircle, 
  Loader2,
  AlertTriangle
} from "lucide-react"

interface ConnectorTestDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  connector?: any
  testResult?: any
  onClose: () => void
}

export function ConnectorTestDialog({ 
  open, 
  onOpenChange, 
  connector, 
  testResult, 
  onClose 
}: ConnectorTestDialogProps) {

  const renderTestResult = () => {
    if (!testResult) {
      return (
        <div className="flex flex-col items-center justify-center py-8">
          <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">Testing connection...</p>
        </div>
      )
    }

    const isSuccess = testResult.connection_valid
    const StatusIcon = isSuccess ? CheckCircle : XCircle
    const statusColor = isSuccess ? "text-green-500" : "text-red-500"

    return (
      <div className="space-y-6">
        <div className="text-center">
          <StatusIcon className={`w-12 h-12 mx-auto mb-4 ${statusColor}`} />
          <h3 className="text-lg font-semibold mb-2">
            Connection {isSuccess ? "Successful" : "Failed"}
          </h3>
          <Badge variant={isSuccess ? "default" : "destructive"} className={isSuccess ? "bg-green-500" : ""}>
            {testResult.status}
          </Badge>
        </div>

        {testResult.error_message && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="font-semibold mb-1">Error Details:</div>
              {testResult.error_message}
            </AlertDescription>
          </Alert>
        )}

        {testResult.test_data && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Connection Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(testResult.test_data).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-sm font-medium capitalize">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {String(value)}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {isSuccess && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Your {connector?.provider} connector is properly configured and ready to sync inventory data.
            </AlertDescription>
          </Alert>
        )}
      </div>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TestTube className="w-5 h-5" />
            Test Connection - {connector?.provider}
          </DialogTitle>
          <DialogDescription>
            Testing the connection to your {connector?.provider} system
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-[200px]">
          {renderTestResult()}
        </div>

        <DialogFooter>
          <Button onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 