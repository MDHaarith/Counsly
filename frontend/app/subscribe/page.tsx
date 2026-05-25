"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Check, ShieldCheck, Sparkles, TriangleAlert } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { createPaymentOrder, verifyPayment } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";
import { buildRazorpayCheckoutOptions, loadRazorpayScript, paywallCopyForSource } from "@/lib/payments.mjs";
import { Badge, Surface } from "@/components/ui";

const features = [
  "All recommendation rows and full official-rank context",
  "Choice filing, snapshots, import, and export",
  "Detailed compare sessions and college evidence panels",
  "Full college insight panels and trend analytics",
];

type RazorpayCheckoutResponse = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

function SubscribeContent() {
  const router = useRouter();
  const params = useSearchParams();
  const { setSubscriptionActive, user } = useApp();
  const source = params.get("from") || "";
  const copy = useMemo(() => paywallCopyForSource(source), [source]);
  const [consent, setConsent] = useState(false);
  const [paid, setPaid] = useState(Boolean(user?.subscription_active));
  const [loading, setLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState("Razorpay opens after consent. No refunds; no auto-renewal.");
  const paywallTracked = useRef(false);

  useEffect(() => {
    if (!paywallTracked.current) {
      paywallTracked.current = true;
      trackFunnelEvent("paywall_seen", { feature: source || "full-access", user });
    }
    if (user?.subscription_active) {
      setPaid(true);
      const target = source && source !== "recommendations" ? `/${source}` : "/dashboard";
      const timer = window.setTimeout(() => router.replace(target), 900);
      return () => window.clearTimeout(timer);
    }
  }, [router, source, user, user?.subscription_active]);

  const unlock = async () => {
    if (!consent) return;
    setLoading(true);
    setPaymentStatus("Creating a secure Razorpay order...");
    trackFunnelEvent("payment_started", {
      amount: 14900,
      feature: source || "full-access",
      user,
    });
    try {
      const order = await createPaymentOrder(source);
      const key = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || order.key_id || "";
      if (!key) throw new Error("Razorpay key is not configured for this frontend build.");
      await loadRazorpayScript();
      const checkout = new (window as any).Razorpay(buildRazorpayCheckoutOptions({
        key,
        order,
        source,
        user,
        verify: async (payload: RazorpayCheckoutResponse) => {
          setPaymentStatus("Verifying payment with Counsly...");
          const verified = await verifyPayment(payload);
          if (!verified.subscription_active) throw new Error(verified.message || "Payment verification did not activate access.");
          setSubscriptionActive(true);
          setPaid(true);
          trackFunnelEvent("payment_completed", {
            amount: 14900,
            feature: source || "full-access",
            user: { ...user, subscription_active: true },
          });
          setPaymentStatus("Full Access active. Redirecting to your workspace...");
        },
      }));
      checkout.on("payment.failed", (event: any) => {
        setPaymentStatus(event?.error?.description || "Payment failed before verification. No access was activated.");
        setLoading(false);
      });
      checkout.open();
    } catch (error) {
      setPaymentStatus(error instanceof Error ? error.message : "Payment could not be started. Try again after checking Razorpay setup.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 py-4">
      <Link className="button-quiet w-fit" href={user ? "/dashboard" : "/"}>
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="space-y-5 py-4">
          <Badge tone="coral">Full Access</Badge>
          <h1 className="display-title">{copy.heading}</h1>
          <p className="copy max-w-2xl">
            {copy.summary} One payment keeps the 2027 Counsly workspace open through the counselling season. No subscription renewal.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {features.map((feature) => (
              <p className="flex min-h-16 items-start gap-2 rounded-xl border border-counsly-line bg-counsly-canvas p-4 text-sm leading-6 text-counsly-body" key={feature}>
                <Check className="mt-1 h-4 w-4 shrink-0 text-counsly-safe" />
                {feature}
              </p>
            ))}
          </div>
        </div>

        <Surface className="space-y-5 p-6 md:p-8" tone={paid ? "dark" : "paper"}>
          {paid ? (
            <>
              <ShieldCheck className="h-10 w-10 text-counsly-safe" />
              <h2 className="font-display text-4xl text-white">Full Access active.</h2>
              <p className="text-sm leading-6 text-counsly-card">
                Return to the workspace and keep filing decisions tied to saved evidence.
              </p>
              <Link className="button-primary" href="/dashboard">Open dashboard</Link>
            </>
          ) : (
            <>
              <Badge>One-time payment</Badge>
              <div>
                <p className="font-mono text-6xl text-counsly-ink">₹149</p>
                <p className="mt-2 text-sm text-counsly-muted">Valid until the TNEA 2026 season ends.</p>
              </div>
              <p className="rounded-xl border border-counsly-line bg-counsly-soft p-4 text-sm leading-6 text-counsly-body">
                <TriangleAlert className="mr-2 inline h-4 w-4 text-counsly-coral" />
                {paymentStatus}
              </p>
              <label className="flex items-start gap-3 rounded-xl bg-counsly-soft p-4 text-sm leading-6 text-counsly-body">
                <input checked={consent} className="mt-1" onChange={(event) => setConsent(event.target.checked)} type="checkbox" />
                I understand that the one-time purchase is final and Counsly does not promise allotment outcomes.
              </label>
              <button className="button-primary w-full" disabled={!consent || loading} onClick={unlock} type="button">
                <Sparkles className="h-4 w-4" /> {loading ? "Opening Razorpay..." : "Pay ₹149 and unlock"}
              </button>
            </>
          )}
        </Surface>
      </div>
    </div>
  );
}

export default function SubscribePage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-5xl py-10 text-sm text-counsly-body">Loading payment context...</div>}>
      <SubscribeContent />
    </Suspense>
  );
}
