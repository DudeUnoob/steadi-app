"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Store, ExternalLink } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useConnectorStore } from "@/stores/connectorStore"

interface ConnectorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  connector?: any
  onClose: () => void
}

export function ConnectorDialog({ open, onOpenChange, connector, onClose }: ConnectorDialogProps) {
  const { toast } = useToast()
  const [provider, setProvider] = useState("")
  const [config, setConfig] = useState<any>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { createConnector, updateConnector, isLoading } = useConnectorStore()

  useEffect(() => {
    if (connector) {
      setProvider(connector.provider)
      setConfig(connector.config || {})
    } else {
      setProvider("")
      setConfig({})
    }
  }, [connector])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      if (connector) {
        await updateConnector(connector.id, config)
        toast({
          title: "Success",
          description: "Connector updated successfully",
        })
      } else {
        await createConnector(provider, config)
        toast({
          title: "Success",
          description: "Connector created successfully",
        })
      }
      onClose()
    } catch (error) {
      // Error is handled by the store
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConfigChange = (key: string, value: string) => {
    setConfig((prev: any) => ({
      ...prev,
      [key]: value
    }))
  }

  const renderProviderFields = () => {
    switch (provider) {
      case 'SHOPIFY':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="access_token">Access Token</Label>
              <Input
                id="access_token"
                type="password"
                placeholder="shpat_xxxxx"
                value={config.access_token || ""}
                onChange={(e) => handleConfigChange("access_token", e.target.value)}
                required
              />
              <p className="text-sm text-muted-foreground">
                Your Shopify private app access token
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="shop_domain">Shop Domain</Label>
              <Input
                id="shop_domain"
                placeholder="mystore.myshopify.com"
                value={config.shop_domain || ""}
                onChange={(e) => handleConfigChange("shop_domain", e.target.value)}
                required
              />
              <p className="text-sm text-muted-foreground">
                Your Shopify store domain (without https://)
              </p>
            </div>
          </div>
        )

      case 'SQUARE':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="access_token">Access Token</Label>
              <Input
                id="access_token"
                type="password"
                placeholder="EAAAxxxxxxxxx"
                value={config.access_token || ""}
                onChange={(e) => handleConfigChange("access_token", e.target.value)}
                required
              />
              <p className="text-sm text-muted-foreground">
                Your Square application access token
              </p>
            </div>
          </div>
        )

      case 'LIGHTSPEED':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="access_token">Access Token</Label>
              <Input
                id="access_token"
                type="password"
                placeholder="Bearer token"
                value={config.access_token || ""}
                onChange={(e) => handleConfigChange("access_token", e.target.value)}
                required
              />
              <p className="text-sm text-muted-foreground">
                Your Lightspeed API access token
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="account_id">Account ID</Label>
              <Input
                id="account_id"
                placeholder="123456"
                value={config.account_id || ""}
                onChange={(e) => handleConfigChange("account_id", e.target.value)}
                required
              />
              <p className="text-sm text-muted-foreground">
                Your Lightspeed account ID
              </p>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  const getProviderInstructions = () => {
    switch (provider) {
      case 'SHOPIFY':
        return (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Setup Instructions</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>1. Go to your Shopify admin panel</p>
              <p>2. Navigate to Apps → Develop apps</p>
              <p>3. Create a private app with inventory read permissions</p>
              <p>4. Copy the access token and your store domain</p>
              <Button variant="link" size="sm" className="p-0 h-auto">
                <ExternalLink className="w-3 h-3 mr-1" />
                View Shopify Documentation
              </Button>
            </CardContent>
          </Card>
        )

      case 'SQUARE':
        return (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Setup Instructions</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>1. Go to Square Developer Dashboard</p>
              <p>2. Create a new application</p>
              <p>3. Generate an access token with inventory permissions</p>
              <p>4. Copy the access token</p>
              <Button variant="link" size="sm" className="p-0 h-auto">
                <ExternalLink className="w-3 h-3 mr-1" />
                View Square Documentation
              </Button>
            </CardContent>
          </Card>
        )

      case 'LIGHTSPEED':
        return (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Setup Instructions</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>1. Contact Lightspeed to get API access</p>
              <p>2. Obtain your account ID and access token</p>
              <p>3. Ensure you have inventory read permissions</p>
              <Button variant="link" size="sm" className="p-0 h-auto">
                <ExternalLink className="w-3 h-3 mr-1" />
                View Lightspeed Documentation
              </Button>
            </CardContent>
          </Card>
        )

      default:
        return null
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Store className="w-5 h-5" />
            {connector ? "Edit Connector" : "Add New Connector"}
          </DialogTitle>
          <DialogDescription>
            {connector 
              ? "Update your connector configuration"
              : "Connect your POS system to automatically sync inventory data"
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!connector && (
            <div className="space-y-2">
              <Label htmlFor="provider">POS Provider</Label>
              <Select value={provider} onValueChange={setProvider} required>
                <SelectTrigger>
                  <SelectValue placeholder="Select your POS system" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SHOPIFY">Shopify</SelectItem>
                  <SelectItem value="SQUARE">Square</SelectItem>
                  <SelectItem value="LIGHTSPEED">Lightspeed Retail</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {provider && (
            <>
              {renderProviderFields()}
              {getProviderInstructions()}
            </>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={!provider || isSubmitting || isLoading}
            >
              {isSubmitting || isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {connector ? "Updating..." : "Creating..."}
                </>
              ) : (
                connector ? "Update Connector" : "Create Connector"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
} 