"use client"

import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { 
  CheckCircle, 
  XCircle, 
  Loader2,
  AlertTriangle,
  Package,
  Plus,
  Edit
} from "lucide-react"

interface ConnectorSyncDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  connector?: any
  syncResult?: any
  isSyncing: boolean
  onClose: () => void
}

export function ConnectorSyncDialog({ 
  open, 
  onOpenChange, 
  connector, 
  syncResult, 
  isSyncing,
  onClose 
}: ConnectorSyncDialogProps) {

  const renderSyncContent = () => {
    if (isSyncing) {
      return (
        <div className="space-y-6">
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Syncing Inventory</h3>
            <p className="text-muted-foreground text-center">
              Fetching data from your {connector?.provider} system...
            </p>
          </div>
          <Progress value={undefined} className="w-full" />
        </div>
      )
    }

    if (!syncResult) {
      return (
        <div className="flex flex-col items-center justify-center py-8">
          {/* <Refresh className="w-12 h-12 text-muted-foreground mb-4" /> */}
          <h3 className="text-lg font-semibold mb-2">Ready to Sync</h3>
          <p className="text-muted-foreground text-center">
            Click sync to fetch the latest inventory data from {connector?.provider}
          </p>
        </div>
      )
    }

    const isSuccess = syncResult.status === 'ACTIVE'
    const StatusIcon = isSuccess ? CheckCircle : XCircle
    const statusColor = isSuccess ? "text-green-500" : "text-red-500"

    return (
      <div className="space-y-6">
        <div className="text-center">
          <StatusIcon className={`w-12 h-12 mx-auto mb-4 ${statusColor}`} />
          <h3 className="text-lg font-semibold mb-2">
            Sync {isSuccess ? "Complete" : "Failed"}
          </h3>
          <Badge variant={isSuccess ? "default" : "destructive"} className={isSuccess ? "bg-green-500" : ""}>
            {syncResult.status}
          </Badge>
        </div>

        {isSuccess && (
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-blue-500" />
                  <div className="text-2xl font-bold text-blue-600">
                    {syncResult.items_synced}
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">Items Synced</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Plus className="w-4 h-4 text-green-500" />
                  <div className="text-2xl font-bold text-green-600">
                    {syncResult.items_created}
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">Items Created</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Edit className="w-4 h-4 text-orange-500" />
                  <div className="text-2xl font-bold text-orange-600">
                    {syncResult.items_updated}
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">Items Updated</p>
              </CardContent>
            </Card>
          </div>
        )}

        {syncResult.sync_started_at && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Sync Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Started:</span>
                <span className="text-sm text-muted-foreground">
                  {new Date(syncResult.sync_started_at).toLocaleString()}
                </span>
              </div>
              {syncResult.sync_completed_at && (
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Completed:</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(syncResult.sync_completed_at).toLocaleString()}
                  </span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Provider:</span>
                <span className="text-sm text-muted-foreground">
                  {syncResult.provider}
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {syncResult.errors && syncResult.errors.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="font-semibold mb-2">Sync Errors ({syncResult.errors.length}):</div>
              <ul className="list-disc list-inside space-y-1">
                {syncResult.errors.slice(0, 5).map((error: string, index: number) => (
                  <li key={index} className="text-sm">{error}</li>
                ))}
                {syncResult.errors.length > 5 && (
                  <li className="text-sm">... and {syncResult.errors.length - 5} more</li>
                )}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {isSuccess && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Successfully synced inventory data from your {connector?.provider} system. 
              Your inventory is now up to date.
            </AlertDescription>
          </Alert>
        )}
      </div>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {/* <Refresh className="w-5 h-5" /> */}
            Sync Inventory - {connector?.provider}
          </DialogTitle>
          <DialogDescription>
            Synchronizing inventory data from your {connector?.provider} system
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-[300px]">
          {renderSyncContent()}
        </div>

        <DialogFooter>
          <Button onClick={onClose} disabled={isSyncing}>
            {isSyncing ? "Syncing..." : "Close"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 