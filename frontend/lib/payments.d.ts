export type PaywallCopy = {
  heading: string;
  summary: string;
};

export type RazorpayOrder = {
  amount: number;
  currency?: string;
  id: string;
  receipt?: string;
};

export type RazorpayCheckoutResponse = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

export function paywallCopyForSource(source?: string): PaywallCopy;

export function buildVerificationPayload(response: RazorpayCheckoutResponse): RazorpayCheckoutResponse;

export function buildRazorpayCheckoutOptions(input: {
  key: string;
  order: RazorpayOrder;
  source?: string;
  user?: { google_email?: string; name?: string } | null;
  verify: (payload: RazorpayCheckoutResponse) => Promise<unknown>;
}): Record<string, unknown>;

export function loadRazorpayScript(doc?: Document): Promise<void>;
