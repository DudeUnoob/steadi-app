"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, Store, Shield } from "lucide-react"
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
  const [setupMethod, setSetupMethod] = useState<"oauth" | "manual">("oauth")
  const [shopDomain, setShopDomain] = useState("")
  const [oauthUrls, setOauthUrls] = useState<any>({})

  const { createConnector, updateConnector, isLoading, getOAuthUrls } = useConnectorStore()

  useEffect(() => {
    if (connector) {
      setProvider(connector.provider)
      setConfig(connector.config || {})
      setSetupMethod("manual") // Existing connectors use manual editing
    } else {
      setProvider("")
      setConfig({})
      setSetupMethod("oauth")
      // Load OAuth URLs when dialog opens
      loadOAuthUrls()
    }
  }, [connector, open])

  const loadOAuthUrls = async () => {
    try {
      const urls = await getOAuthUrls()
      setOauthUrls(urls)
    } catch (error) {
      console.error("Failed to load OAuth URLs:", error)
    }
  }

  const handleOAuthConnect = (provider: string) => {
    if (!oauthUrls[provider.toLowerCase()]) {
      toast({
        title: "Error",
        description: `${provider} OAuth is not configured`,
        variant: "destructive"
      })
      return
    }

    const providerConfig = oauthUrls[provider.toLowerCase()]
    let authUrl = providerConfig.auth_url

    // Build OAuth URL with parameters
    const params = new URLSearchParams({
      client_id: providerConfig.client_id,
      redirect_uri: providerConfig.redirect_uri,
      scope: providerConfig.scopes,
      response_type: "code",
      state: `${provider.toLowerCase()}_${Date.now()}` // CSRF protection
    })

    // Special handling for Shopify - need shop domain
    if (provider === "SHOPIFY") {
      if (!shopDomain) {
        toast({
          title: "Error",
          description: "Please enter your shop domain first",
          variant: "destructive"
        })
        return
      }
      authUrl = authUrl.replace("{shop_domain}", shopDomain)
    }

    const finalUrl = `${authUrl}?${params.toString()}`
    
    // Store provider and shop domain for callback
    sessionStorage.setItem("steadi_oauth_provider", provider)
    if (shopDomain) {
      sessionStorage.setItem("steadi_oauth_shop_domain", shopDomain)
    }

    // Open OAuth flow in same window
    window.location.href = finalUrl
  }

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

  const renderOAuthOption = (providerName: string, description: string, available: boolean) => {
    return (
      <Card className={`cursor-pointer transition-colors ${!available ? 'opacity-50' : 'hover:border-primary'}`}>
        <CardContent className="p-6">
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <Store className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-medium">{providerName}</h3>
                {available && <Shield className="h-4 w-4 text-green-500" />}
              </div>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
            <div className="flex-shrink-0">
              {available ? (
                providerName === "Shopify" ? (
                  <div className="space-y-2">
                    <Input
                      placeholder="mystore.myshopify.com"
                      value={shopDomain}
                      onChange={(e) => setShopDomain(e.target.value)}
                      className="w-48"
                    />
                    <Button 
                      onClick={() => handleOAuthConnect("SHOPIFY")}
                      disabled={!shopDomain}
                      className="w-full"
                    >
                      Connect Shopify
                    </Button>
                  </div>
                ) : (
                  <Button onClick={() => handleOAuthConnect(providerName.toUpperCase())}>
                    Connect {providerName}
                  </Button>
                )
              ) : (
                <Button variant="outline" disabled>
                  Not Available
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    )
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

  // If no connector (new connection), show OAuth wizard
  if (!connector && setupMethod === "oauth") {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Connect Your POS System</DialogTitle>
            <DialogDescription>
              Choose your point of sale system and connect securely with OAuth
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {renderOAuthOption(
              "Shopify", 
              "Connect your Shopify store to automatically sync inventory", 
              !!oauthUrls.shopify
            )}
            {renderOAuthOption(
              "Square", 
              "Connect your Square POS to sync inventory and sales data", 
              !!oauthUrls.square
            )}
            {renderOAuthOption(
              "Lightspeed", 
              "Connect your Lightspeed Retail system for inventory management", 
              !!oauthUrls.lightspeed
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSetupMethod("manual")}
            >
              Manual Setup Instead
            </Button>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  // Manual setup or editing existing connector
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {connector ? "Edit Connector" : "Manual Connector Setup"}
          </DialogTitle>
          <DialogDescription>
            {connector 
              ? "Update your connector configuration" 
              : "Manually configure your POS system connection"
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!connector && (
            <div className="space-y-2">
              <Label htmlFor="provider">Provider</Label>
              <Select value={provider} onValueChange={setProvider} required>
                <SelectTrigger>
                  <SelectValue placeholder="Select a provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SHOPIFY">Shopify</SelectItem>
                  <SelectItem value="SQUARE">Square</SelectItem>
                  <SelectItem value="LIGHTSPEED">Lightspeed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {provider && renderProviderFields()}

          <DialogFooter>
            {!connector && setupMethod === "manual" && (
              <Button
                type="button"
                variant="outline"
                onClick={() => setSetupMethod("oauth")}
              >
                Use OAuth Instead
              </Button>
            )}
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || isLoading}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {connector ? "Update" : "Create"} Connector
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
} 