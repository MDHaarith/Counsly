"use client";

import Link from "next/link";
import Script from "next/script";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiClient, postJson } from "@/lib/api";

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void };
  }
}

interface OrderPayload {
  order_id: string;
  amount_paise: number;
  currency: string;
  key_id: string;
}

export function SubscribeClient() {
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function pay() {
    setLoading(true);
    setError(null);
    try {
      const order = await postJson<OrderPayload>("/api/payments/order", {});
      if (!window.Razorpay) {
        setError("Razorpay checkout is still loading. Try again in a moment.");
        setLoading(false);
        return;
      }
      const checkout = new window.Razorpay({
        key: order.key_id,
        amount: order.amount_paise,
        currency: order.currency,
        name: "Counsly",
        description: "Full Access for this TNEA season",
        order_id: order.order_id,
        handler: async (response: Record<string, string>) => {
          await apiClient("/api/payments/verify", {
            method: "POST",
            body: JSON.stringify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            }),
          });
          setSuccess(true);
          setTimeout(() => {
            window.location.href = "/dashboard";
          }, 1200);
        },
      });
      checkout.open();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment could not start.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="afterInteractive" />
      <div className="space-y-5">
        <Card variant="featured">
          <ul className="space-y-2 text-sm text-olive-gray">
            <li>All recommendations and filters</li>
            <li>200 choice rows with notes</li>
            <li>PDF choice-list export</li>
          </ul>
        </Card>
        <label className="flex min-h-12 items-start gap-3 text-sm leading-relaxed text-olive-gray">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-1 h-6 w-6 shrink-0"
          />
          I understand this is a one-time seasonal purchase and refunds are not handled in-app.
        </label>
        {success && (
          <Card>
            <p className="text-sm text-safe">Payment verified. Redirecting to your dashboard...</p>
          </Card>
        )}
        {error && <p className="text-sm text-error-crimson">{error}</p>}
        <Button onClick={pay} disabled={!consent || loading}>
          {loading ? "Starting payment..." : "Pay ₹149"}
        </Button>
        <Link href="/dashboard">
          <Button variant="ghost">Back to dashboard</Button>
        </Link>
      </div>
    </>
  );
}
