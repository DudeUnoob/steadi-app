import { useEffect, useState } from 'react'
import { useAlertsStore } from '@/stores/alertsStore'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/use-toast'
import { 
  AlertTriangle, 
  AlertCircle, 
  Mail, 
  Bell, 
  RefreshCw, 
  Clock,
  Package,
  TrendingDown,
  CheckCircle2,
  X,
  MailCheck
} from 'lucide-react'

function AlertsDashboard() {
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState('alerts')
  
  const {
    alerts,
    notifications,
    alertSummary,
    rateLimitStatus,
    isLoading,
    isNotificationsLoading,
    isSendingEmail,
    error,
    emailError,
    fetchAlerts,
    fetchNotifications,
    fetchAlertSummary,
    sendEmailAlerts,
    markNotificationRead,
    markAllNotificationsRead,
    deleteNotification,
    resetErrors
  } = useAlertsStore()

  useEffect(() => {
    // Initial data fetch
    fetchAlertSummary()
    fetchAlerts()
    fetchNotifications()
  }, [])

  const handleSendEmail = async () => {
    const success = await sendEmailAlerts()
    if (success) {
      toast({
        title: "Email Sent",
        description: "Stock alert email has been sent successfully.",
      })
    } else {
      toast({
        title: "Email Failed",
        description: emailError || "Failed to send email alert.",
        variant: "destructive",
      })
    }
  }

  const handleMarkAllRead = async () => {
    const success = await markAllNotificationsRead()
    if (success) {
      toast({
        title: "Notifications Updated",
        description: "All notifications marked as read.",
      })
    }
  }

  const handleRefresh = () => {
    resetErrors()
    fetchAlertSummary()
    fetchAlerts()
    fetchNotifications()
  }

  const getAlertBadgeVariant = (alertLevel: string) => {
    switch (alertLevel) {
      case 'RED':
        return 'destructive'
      case 'YELLOW':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  const getAlertIcon = (alertLevel: string) => {
    switch (alertLevel) {
      case 'RED':
        return <AlertTriangle className="h-4 w-4" />
      case 'YELLOW':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <Package className="h-4 w-4" />
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Stock Alerts</h1>
          <p className="text-muted-foreground">
            Monitor inventory levels and manage reorder notifications
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={handleSendEmail}
            disabled={isSendingEmail || rateLimitStatus?.is_limited}
            size="sm"
          >
            <Mail className={`h-4 w-4 mr-2 ${isSendingEmail ? 'animate-pulse' : ''}`} />
            {isSendingEmail ? 'Sending...' : 'Send Email Alert'}
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      {alertSummary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Urgent Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">
                {alertSummary.alert_counts.red}
              </div>
              <p className="text-xs text-muted-foreground">
                Products need immediate reordering
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Warning Alerts</CardTitle>
              <AlertCircle className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {alertSummary.alert_counts.yellow}
              </div>
              <p className="text-xs text-muted-foreground">
                Products approaching reorder point
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unread Notifications</CardTitle>
              <Bell className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {alertSummary.unread_notifications}
              </div>
              <p className="text-xs text-muted-foreground">
                New notifications to review
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Email Rate Limit</CardTitle>
              <MailCheck className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {rateLimitStatus?.requests_remaining || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Emails remaining this minute
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Rate Limit Warning */}
      {rateLimitStatus?.is_limited && (
        <Alert variant="destructive">
          <Clock className="h-4 w-4" />
          <AlertDescription>
            Email rate limit reached. You can send more emails in{' '}
            {rateLimitStatus.reset_time 
              ? Math.ceil((rateLimitStatus.reset_time - Date.now() / 1000) / 60)
              : 1
            } minute(s).
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="alerts">
            Stock Alerts
            {alertSummary && (alertSummary.alert_counts.red + alertSummary.alert_counts.yellow) > 0 && (
              <Badge variant="destructive" className="ml-2">
                {alertSummary.alert_counts.red + alertSummary.alert_counts.yellow}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="notifications">
            Notifications
            {alertSummary && alertSummary.unread_notifications > 0 && (
              <Badge variant="secondary" className="ml-2">
                {alertSummary.unread_notifications}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Products Requiring Attention</CardTitle>
              <CardDescription>
                Products that are at or below their reorder points
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                  Loading alerts...
                </div>
              ) : alerts.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium">All Good!</h3>
                  <p className="text-muted-foreground">
                    No products currently need reordering.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          {getAlertIcon(alert.alert_level)}
                          <Badge variant={getAlertBadgeVariant(alert.alert_level)}>
                            {alert.alert_level}
                          </Badge>
                        </div>
                        <div>
                          <h4 className="font-medium">{alert.sku}</h4>
                          <p className="text-sm text-muted-foreground">{alert.name}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-6 text-sm">
                        <div className="text-center">
                          <p className="font-medium">{alert.on_hand}</p>
                          <p className="text-muted-foreground">On Hand</p>
                        </div>
                        <div className="text-center">
                          <p className="font-medium">{alert.reorder_point}</p>
                          <p className="text-muted-foreground">Reorder Point</p>
                        </div>
                        <div className="text-center">
                          <p className="font-medium">{alert.days_of_stock}</p>
                          <p className="text-muted-foreground">Days Left</p>
                        </div>
                        <div className="text-center">
                          <p className="font-medium">{alert.reorder_quantity}</p>
                          <p className="text-muted-foreground">Suggested Order</p>
                        </div>
                        {alert.supplier_name && (
                          <div className="text-center">
                            <p className="font-medium">{alert.supplier_name}</p>
                            <p className="text-muted-foreground">Supplier</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Notifications</CardTitle>
                <CardDescription>
                  Your alert history and email notifications
                </CardDescription>
              </div>
              {notifications.some(n => !n.read_at) && (
                <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
                  Mark All Read
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {isNotificationsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                  Loading notifications...
                </div>
              ) : notifications.length === 0 ? (
                <div className="text-center py-8">
                  <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium">No Notifications</h3>
                  <p className="text-muted-foreground">
                    You'll see alert notifications here when they're generated.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`flex items-start justify-between p-4 border rounded-lg ${
                        !notification.read_at ? 'bg-blue-50 border-blue-200' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="mt-1">
                          {notification.channel === 'EMAIL' ? (
                            <Mail className="h-4 w-4 text-blue-500" />
                          ) : (
                            <Bell className="h-4 w-4 text-gray-500" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">
                            {notification.payload.message || 'Stock Alert'}
                          </p>
                          <div className="flex items-center space-x-4 mt-1 text-xs text-muted-foreground">
                            <span>{formatTimeAgo(notification.sent_at)}</span>
                            <Badge variant="outline" className="text-xs">
                              {notification.channel}
                            </Badge>
                            {!notification.read_at && (
                              <Badge variant="secondary" className="text-xs">
                                Unread
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {!notification.read_at && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => markNotificationRead(notification.id)}
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteNotification(notification.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AlertsDashboard 