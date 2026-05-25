"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertCircle, Bell, BellOff, Calendar, X } from "lucide-react";

import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { dismissNotification, fetchNotifications, fetchUnreadCount } from "@/lib/api.mjs";

type Notification = {
  id: string;
  event_type?: string;
  summary?: string;
  created_at?: string;
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dismissing, setDismissing] = useState<Set<string>>(new Set());

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [notifs, count] = await Promise.all([
        fetchNotifications(),
        fetchUnreadCount(),
      ]);
      setNotifications(Array.isArray(notifs) ? notifs : []);
      setUnreadCount(typeof count === "number" ? count : count?.unread ?? 0);
    } catch {
      setError("Notifications could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDismiss = async (id: string) => {
    setDismissing((prev) => new Set(prev).add(id));
    try {
      await dismissNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // silently fail — the notification stays visible
    } finally {
      setDismissing((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const eventIcon = (eventType?: string) => {
    switch (eventType) {
      case "choice_update":
      case "choice_created":
        return "📋";
      case "round_start":
      case "round_end":
        return "🏁";
      case "compare_saved":
        return "⚖️";
      case "data_refresh":
        return "🔄";
      case "admin_update":
        return "⚙️";
      case "payment":
        return "💳";
      default:
        return "📬";
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        description="Recent activity and updates from your workspace, choices, rounds, and data changes."
        eyebrow="Activity Centre"
        title="Notifications."
      />

      <div className="grid gap-3 sm:grid-cols-2">
        <Metric label="Total notifications" value={`${notifications.length}`} note="In your workspace" />
        <Surface className="flex items-center gap-3 p-4" tone="paper">
          {unreadCount > 0 ? (
            <>
              <Bell className="h-5 w-5 text-counsly-coral" />
              <div>
                <p className="font-mono text-2xl font-semibold text-counsly-ink">{unreadCount}</p>
                <p className="text-sm text-counsly-muted">Unread notifications</p>
              </div>
            </>
          ) : (
            <>
              <BellOff className="h-5 w-5 text-counsly-muted" />
              <div>
                <p className="font-mono text-2xl font-semibold text-counsly-ink">0</p>
                <p className="text-sm text-counsly-muted">All caught up</p>
              </div>
            </>
          )}
        </Surface>
      </div>

      {loading && (
        <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
          Loading notifications...
        </p>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {notifications.length === 0 ? (
            <Surface className="flex flex-col items-center gap-4 py-12" tone="soft">
              <BellOff className="h-12 w-12 text-counsly-muted" />
              <div className="text-center">
                <h2 className="font-display text-xl text-counsly-ink">No notifications yet</h2>
                <p className="mt-1 text-sm text-counsly-muted">
                  Activity from your choices, compares, rounds, and data updates will appear here.
                </p>
              </div>
            </Surface>
          ) : (
            <div className="space-y-3">
              {notifications.map((notif) => (
                <Surface className="flex items-start gap-4 p-4" key={notif.id} tone="paper">
                  <span className="mt-0.5 text-lg">{eventIcon(notif.event_type)}</span>
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <Badge tone={notif.event_type ? "neutral" : "warning"}>
                        {(notif.event_type ?? "general").replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <p className="text-sm leading-6 text-counsly-body">
                      {notif.summary || "No additional details available."}
                    </p>
                    {notif.created_at && (
                      <div className="mt-2 flex items-center gap-1 text-xs text-counsly-muted">
                        <Calendar className="h-3 w-3" />
                        <span>{new Date(notif.created_at).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                  <button
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-counsly-muted hover:bg-counsly-card hover:text-counsly-coral disabled:opacity-50"
                    disabled={dismissing.has(notif.id)}
                    onClick={() => handleDismiss(notif.id)}
                    title="Dismiss notification"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </Surface>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}