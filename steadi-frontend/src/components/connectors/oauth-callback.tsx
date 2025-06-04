"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2, CheckCircle, XCircle, ArrowLeft } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { useConnectorStore } from "@/stores/connectorStore"

export function OAuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
  const [message, setMessage] = useState("")
  const [connectorInfo, setConnectorInfo] = useState<any>(null)

  const { initializeOAuth } = useConnectorStore()

  useEffect(() => {
    handleOAuthCallback()
  }, [])

  const handleOAuthCallback = async () => {
    try {
      const code = searchParams.get("code")
      const state = searchParams.get("state")
      const error = searchParams.get("error")
      const errorDescription = searchParams.get("error_description")

      if (error) {
        setStatus("error")
        setMessage(`OAuth error: ${error}${errorDescription ? ` - ${errorDescription}` : ''}`)
        return
      }

      if (!code || !state) {
        setStatus("error")
        setMessage("Missing OAuth parameters (code or state)")
        return
      }

      // Get provider from state or session storage
      const provider = sessionStorage.getItem("steadi_oauth_provider")
      const shopDomain = sessionStorage.getItem("steadi_oauth_shop_domain")

      if (!provider) {
        setStatus("error")
        setMessage("Missing provider information. Please try connecting again.")
        return
      }

      // Verify state matches (basic CSRF protection)
      if (!state.startsWith(provider.toLowerCase())) {
        setStatus("error")
        setMessage("Invalid state parameter. Possible security issue.")
        return
      }

      console.log(`Initializing OAuth for ${provider} with code: ${code.substring(0, 10)}...`)

      // Initialize OAuth with backend
      const result = await initializeOAuth(provider, {
        oauth_code: code,
        shop_domain: shopDomain || undefined,
        state: state
      })

      setConnectorInfo(result)
      setStatus("success")
      setMessage(result.message)

      // Clean up session storage
      sessionStorage.removeItem("steadi_oauth_provider")
      sessionStorage.removeItem("steadi_oauth_shop_domain")

      // Show success toast
      toast({
        title: "Success!",
        description: `${provider} connector connected successfully`,
      })

      // Auto-redirect after 3 seconds on success
      setTimeout(() => {
        navigate("/connectors")
      }, 3000)

    } catch (error: any) {
      console.error("OAuth callback error:", error)
      setStatus("error")
      setMessage(error.message || "Failed to complete OAuth flow")
      
      toast({
        title: "Connection Failed",
        description: error.message || "Failed to connect your POS system",
        variant: "destructive"
      })
    }
  }

  const handleReturnToConnectors = () => {
    navigate("/connectors")
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            {status === "loading" && (
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
            )}
            {status === "success" && (
              <CheckCircle className="h-12 w-12 text-green-500" />
            )}
            {status === "error" && (
              <XCircle className="h-12 w-12 text-red-500" />
            )}
          </div>
          
          <CardTitle>
            {status === "loading" && "Connecting your POS system..."}
            {status === "success" && "Successfully Connected!"}
            {status === "error" && "Connection Failed"}
          </CardTitle>
          
          <CardDescription className="mt-2">
            {status === "loading" && "Please wait while we complete the setup"}
            {status === "success" && "Your POS system is now connected to Steadi. Redirecting..."}
            {status === "error" && "There was a problem connecting your POS system"}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {message && (
            <div className={`p-3 rounded-md text-sm ${
              status === "success" 
                ? "bg-green-50 text-green-800 border border-green-200"
                : status === "error"
                ? "bg-red-50 text-red-800 border border-red-200"
                : "bg-blue-50 text-blue-800 border border-blue-200"
            }`}>
              {message}
            </div>
          )}

          {connectorInfo && status === "success" && (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Provider:</span>
                <span className="font-medium">{connectorInfo.provider}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status:</span>
                <span className={`font-medium ${
                  connectorInfo.status === "ACTIVE" ? "text-green-600" : "text-yellow-600"
                }`}>
                  {connectorInfo.status}
                </span>
              </div>
              {status === "success" && (
                <div className="text-xs text-muted-foreground mt-2">
                  Automatically redirecting in 3 seconds...
                </div>
              )}
            </div>
          )}

          {status !== "loading" && (
            <Button 
              onClick={handleReturnToConnectors}
              className="w-full"
              variant={status === "success" ? "default" : "outline"}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Return to Connectors
            </Button>
          )}

          {status === "error" && (
            <Button 
              onClick={() => navigate("/connectors")}
              variant="default"
              className="w-full"
            >
              Try Again
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 