import { useEffect } from 'react'
import { useAlertsStore } from '@/stores/alertsStore'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Bell, AlertTriangle, AlertCircle, Mail, Eye, Trash2 } from 'lucide-react'

interface NotificationBellProps {
  className?: string
  showDropdown?: boolean
}

function NotificationBell({ className = '', showDropdown = true }: NotificationBellProps) {
  const {
    notifications,
    alertSummary,
    isNotificationsLoading,
    fetchAlertSummary,
    fetchNotifications,
    markNotificationRead,
    deleteNotification
  } = useAlertsStore()

  useEffect(() => {
    // Fetch initial data
    fetchAlertSummary()
    fetchNotifications(false, 5) // Only get recent unread notifications
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchAlertSummary()
      fetchNotifications(false, 5)
    }, 30000) // Poll every 30 seconds
    
    return () => clearInterval(interval)
  }, [])

  const unreadCount = alertSummary?.unread_notifications || 0
  const recentNotifications = notifications.slice(0, 5)

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  const getNotificationIcon = (notification: any) => {
    if (notification.channel === 'EMAIL') {
      return <Mail className="h-4 w-4 text-blue-500" />
    }
    
    const alertLevel = notification.payload?.alert_level
    if (alertLevel === 'RED') {
      return <AlertTriangle className="h-4 w-4 text-red-500" />
    } else if (alertLevel === 'YELLOW') {
      return <AlertCircle className="h-4 w-4 text-yellow-500" />
    }
    
    return <Bell className="h-4 w-4 text-gray-500" />
  }

  const handleMarkAsRead = async (notificationId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    await markNotificationRead(notificationId)
  }

  const handleDelete = async (notificationId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    await deleteNotification(notificationId)
  }

  if (!showDropdown) {
    // Simple bell icon for sidebar
    return (
      <div className={`relative ${className}`}>
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <Badge 
            variant="destructive" 
            className="absolute -top-2 -right-2 h-5 w-5 flex items-center justify-center text-xs p-0"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </Badge>
        )}
      </div>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className={`relative ${className}`}>
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge 
              variant="destructive" 
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center text-xs p-0"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {unreadCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {unreadCount} unread
            </Badge>
          )}
        </DropdownMenuLabel>
        
        <DropdownMenuSeparator />
        
        {isNotificationsLoading ? (
          <DropdownMenuItem disabled>
            <div className="flex items-center space-x-2">
              <Bell className="h-4 w-4 animate-pulse" />
              <span>Loading notifications...</span>
            </div>
          </DropdownMenuItem>
        ) : recentNotifications.length === 0 ? (
          <DropdownMenuItem disabled>
            <div className="flex flex-col items-center space-y-2 py-4">
              <Bell className="h-8 w-8 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">No notifications</span>
            </div>
          </DropdownMenuItem>
        ) : (
          <>
            {recentNotifications.map((notification) => (
              <DropdownMenuItem
                key={notification.id}
                className={`flex items-start space-x-3 p-3 cursor-pointer ${
                  !notification.read_at ? 'bg-blue-50' : ''
                }`}
                onClick={() => !notification.read_at && markNotificationRead(notification.id)}
              >
                <div className="mt-0.5">
                  {getNotificationIcon(notification)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {notification.payload.message || 'Stock Alert'}
                  </p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-muted-foreground">
                      {formatTimeAgo(notification.sent_at)}
                    </span>
                    <div className="flex items-center space-x-1">
                      {!notification.read_at && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={(e) => handleMarkAsRead(notification.id, e)}
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={(e) => handleDelete(notification.id, e)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </DropdownMenuItem>
            ))}
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem asChild>
              <a 
                href="/alerts" 
                className="text-center text-sm text-blue-600 hover:text-blue-800 cursor-pointer"
              >
                View all notifications
              </a>
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default NotificationBell 