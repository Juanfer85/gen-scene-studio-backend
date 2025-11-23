import React, { useEffect } from 'react';
import { toast } from 'sonner';
import { X, CheckCircle, XCircle, AlertTriangle, Info, Bell } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useJobsStore } from '@/store/jobsStore';
import { JobNotification } from '@/types/job';

interface CustomToastProps {
  notification: JobNotification;
  onClose: () => void;
}

const CustomToast: React.FC<CustomToastProps> = ({ notification, onClose }) => {
  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBgColor = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -50, scale: 0.95 }}
      className={clsx(
        "relative flex items-start gap-3 p-4 rounded-lg border shadow-lg max-w-sm",
        getBgColor()
      )}
    >
      {getIcon()}
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-semibold text-gray-900 mb-1">
          {notification.title}
        </h4>
        <p className="text-sm text-gray-600">{notification.message}</p>
        {notification.jobId && (
          <p className="text-xs text-gray-500 mt-1">
            Job ID: {notification.jobId}
          </p>
        )}
      </div>
      <button
        onClick={onClose}
        className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
};

export const NotificationToast: React.FC = () => {
  const { notifications, markNotificationRead, clearNotifications } = useJobsStore();

  // Show toasts for new notifications
  useEffect(() => {
    const unreadNotifications = notifications.filter(n => !n.read);
    unreadNotifications.forEach(notification => {
      toast.custom((id) => (
        <CustomToast
          notification={notification}
          onClose={() => {
            toast.dismiss(id);
            markNotificationRead(notification.id);
          }}
        />
      ), {
        duration: 5000, // 5 seconds
        position: 'top-right',
      });
    });
  }, [notifications, markNotificationRead]);

  return null;
};

interface NotificationCenterProps {
  className?: string;
  maxVisible?: number;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  className,
  maxVisible = 5,
}) => {
  const {
    notifications,
    markNotificationRead,
    clearNotifications,
  } = useJobsStore();

  const [isOpen, setIsOpen] = React.useState(false);
  const unreadCount = notifications.filter(n => !n.read).length;

  const visibleNotifications = notifications.slice(0, maxVisible);

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={clsx("relative", className)}>
      {/* Notification Bell */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-500 hover:text-gray-700 transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </motion.div>
        )}
      </motion.button>

      {/* Notification Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute right-0 mt-2 w-80 bg-white rounded-lg border border-gray-200 shadow-xl z-50 max-h-96 overflow-hidden"
          >
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">Notifications</h3>
                {notifications.length > 0 && (
                  <button
                    onClick={clearNotifications}
                    className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
              {unreadCount > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
                </p>
              )}
            </div>

            <div className="overflow-y-auto max-h-64">
              {visibleNotifications.length === 0 ? (
                <div className="p-4 text-center">
                  <Bell className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No notifications</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  <AnimatePresence>
                    {visibleNotifications.map((notification) => (
                      <motion.div
                        key={notification.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className={clsx(
                          "p-3 hover:bg-gray-50 transition-colors cursor-pointer",
                          !notification.read && "bg-blue-50"
                        )}
                        onClick={() => markNotificationRead(notification.id)}
                      >
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 mt-0.5">
                            {notification.type === 'success' && <CheckCircle className="w-4 h-4 text-green-500" />}
                            {notification.type === 'error' && <XCircle className="w-4 h-4 text-red-500" />}
                            {notification.type === 'warning' && <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                            {notification.type === 'info' && <Info className="w-4 h-4 text-blue-500" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900">
                              {notification.title}
                            </p>
                            <p className="text-xs text-gray-600 mt-0.5">
                              {notification.message}
                            </p>
                            {notification.jobId && (
                              <p className="text-xs text-gray-500 mt-1">
                                Job: {notification.jobId}
                              </p>
                            )}
                            <p className="text-xs text-gray-400 mt-1">
                              {formatTimestamp(notification.timestamp)}
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </div>

            {notifications.length > maxVisible && (
              <div className="p-3 border-t border-gray-200 text-center">
                <p className="text-xs text-gray-500">
                  +{notifications.length - maxVisible} more notifications
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Overlay */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

// Notification Provider Component
export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { notifications, addNotification } = useJobsStore();

  // Set up global notification handlers
  useEffect(() => {
    // Custom notification function that can be called globally
    (window as any).showNotification = (
      type: 'success' | 'error' | 'warning' | 'info',
      title: string,
      message: string,
      jobId?: string
    ) => {
      addNotification({
        type,
        title,
        message,
        jobId,
      });
    };
  }, [addNotification]);

  return (
    <>
      <NotificationToast />
      {children}
    </>
  );
};

export default NotificationCenter;