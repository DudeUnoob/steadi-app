"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Plus, 
  RefreshCw, 
  Settings, 
  Trash2, 
  TestTube, 
  Upload,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Store,
  FileText
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useConnectorStore } from "@/stores/connectorStore"
import { ConnectorDialog } from "./connector-dialog"
import { CSVUploadDialog } from "./csv-upload-dialog"
import { ConnectorTestDialog } from "./connector-test-dialog"
import { ConnectorSyncDialog } from "./connector-sync-dialog"

export function ConnectorsDashboard() {
  const { toast } = useToast()
  const [selectedConnector, setSelectedConnector] = useState<any>(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showCSVDialog, setShowCSVDialog] = useState(false)
  const [showTestDialog, setShowTestDialog] = useState(false)
  const [showSyncDialog, setShowSyncDialog] = useState(false)

  const {
    connectors,
    isLoading,
    isSyncing,
    error,
    syncResult,
    testResult,
    fetchConnectors,
    deleteConnector,
    syncConnector,
    testConnector,
    resetError,
    resetResults
  } = useConnectorStore()

  useEffect(() => {
    fetchConnectors()
  }, [fetchConnectors])

  useEffect(() => {
    if (error) {
      toast({
        title: "Error",
        description: error,
        variant: "destructive",
      })
      resetError()
    }
  }, [error, toast, resetError])

  const handleDeleteConnector = async (id: string) => {
    try {
      await deleteConnector(id)
      toast({
        title: "Success",
        description: "Connector deleted successfully",
      })
    } catch (error) {
      // Error is handled by the store
    }
  }

  const handleSyncConnector = async (connector: any) => {
    setSelectedConnector(connector)
    setShowSyncDialog(true)
    await syncConnector(connector.id)
  }

  const handleTestConnector = async (connector: any) => {
    setSelectedConnector(connector)
    setShowTestDialog(true)
    await testConnector(connector.id)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Active</Badge>
      case 'ERROR':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Error</Badge>
      case 'PENDING':
        return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />Pending</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'SHOPIFY':
      case 'SQUARE':
      case 'LIGHTSPEED':
        return <Store className="w-5 h-5" />
      case 'CSV':
        return <FileText className="w-5 h-5" />
      default:
        return <Store className="w-5 h-5" />
    }
  }

  const posConnectors = connectors.filter(c => c.provider !== 'CSV')
  const csvUploads = connectors.filter(c => c.provider === 'CSV')

  if (isLoading && connectors.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
          <p>Loading connectors...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Connectors</h1>
          <p className="text-muted-foreground">
            Connect your POS systems and import inventory data
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchConnectors()}
            disabled={isLoading}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setShowCSVDialog(true)}
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload CSV
          </Button>
          <Button
            size="sm"
            onClick={() => setShowCreateDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Connector
          </Button>
        </div>
      </div>

      <Tabs defaultValue="pos" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pos" className="flex items-center gap-2">
            <Store className="h-4 w-4" />
            POS Systems ({posConnectors.length})
          </TabsTrigger>
          <TabsTrigger value="csv" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            CSV Imports ({csvUploads.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pos" className="space-y-4">
          {posConnectors.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Store className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No POS connectors</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Connect your POS system to automatically sync inventory data
                </p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Your First Connector
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {posConnectors.map((connector) => (
                <Card key={connector.id}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-2">
                      {getProviderIcon(connector.provider)}
                      <CardTitle className="text-lg">{connector.provider}</CardTitle>
                    </div>
                    {getStatusBadge(connector.status)}
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {connector.last_sync && (
                        <div className="text-sm text-muted-foreground">
                          Last sync: {new Date(connector.last_sync).toLocaleDateString()}
                        </div>
                      )}
                      
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleTestConnector(connector)}
                          disabled={isLoading}
                        >
                          <TestTube className="w-4 h-4 mr-1" />
                          Test
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSyncConnector(connector)}
                          disabled={isSyncing}
                        >
                          {isSyncing ? (
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                          ) : (
                            <RefreshCw className="w-4 h-4 mr-1" />
                          )}
                          Sync
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedConnector(connector)
                            setShowCreateDialog(true)
                          }}
                        >
                          <Settings className="w-4 h-4 mr-1" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteConnector(connector.id)}
                          disabled={isLoading}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="csv" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>CSV Import</CardTitle>
              <CardDescription>
                Upload a CSV file to import inventory data. Supported formats include SKU, name, quantity, cost, and supplier information.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setShowCSVDialog(true)}>
                <Upload className="w-4 h-4 mr-2" />
                Upload CSV File
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <ConnectorDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        connector={selectedConnector}
        onClose={() => {
          setSelectedConnector(null)
          setShowCreateDialog(false)
        }}
      />

      <CSVUploadDialog
        open={showCSVDialog}
        onOpenChange={setShowCSVDialog}
      />

      <ConnectorTestDialog
        open={showTestDialog}
        onOpenChange={setShowTestDialog}
        connector={selectedConnector}
        testResult={testResult}
        onClose={() => {
          setShowTestDialog(false)
          setSelectedConnector(null)
          resetResults()
        }}
      />

      <ConnectorSyncDialog
        open={showSyncDialog}
        onOpenChange={setShowSyncDialog}
        connector={selectedConnector}
        syncResult={syncResult}
        isSyncing={isSyncing}
        onClose={() => {
          setShowSyncDialog(false)
          setSelectedConnector(null)
          resetResults()
        }}
      />
    </div>
  )
} 