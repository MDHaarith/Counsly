const copyBySource = {
  analytics: {
    heading: "Trend Analytics requires Full Access.",
    summary: "Unlock cutoff trend boards, risk bands, and the full analytics layer before finalising priorities.",
  },
  choices: {
    heading: "Choice Filing requires Full Access.",
    summary: "Use the primary choice workspace with drag ordering, notes, snapshots, CSV import, and PDF export.",
  },
  compare: {
    heading: "Full compare and college details require Full Access.",
    summary: "Open the full compare table, paid evidence rows, and saved comparison sessions.",
  },
  explore: {
    heading: "Full compare and college details require Full Access.",
    summary: "Unlock placement, community-seat, facility, and add-to-choice actions from college insight.",
  },
  recommendations: {
    heading: "Showing 3 of X colleges. Unlock all for ₹149.",
    summary: "Review every fit-ranked recommendation row and save targets into your choice filing workspace.",
  },
};

export function paywallCopyForSource(source = "") {
  return copyBySource[source] || {
    heading: "Unlock Full Access for ₹149.",
    summary: "Open all Counsly decision surfaces for the current TNEA counselling season.",
  };
}

export function buildVerificationPayload(response) {
  return {
    razorpay_order_id: response.razorpay_order_id,
    razorpay_payment_id: response.razorpay_payment_id,
    razorpay_signature: response.razorpay_signature,
  };
}

export function buildRazorpayCheckoutOptions({ key, order, source = "", user, verify }) {
  const copy = paywallCopyForSource(source);
  return {
    amount: order.amount,
    currency: order.currency || "INR",
    description: copy.heading,
    handler: (response) => verify(buildVerificationPayload(response)),
    key,
    name: "Counsly",
    notes: {
      feature: source || "full-access",
      policy: "no-refunds",
    },
    order_id: order.id,
    prefill: {
      email: user?.google_email || "",
      name: user?.name || "",
    },
    readonly: {
      email: Boolean(user?.google_email),
      name: Boolean(user?.name),
    },
    theme: {
      color: "#CC785C",
    },
  };
}

export function loadRazorpayScript(doc = globalThis.document) {
  if (!doc) return Promise.reject(new Error("Razorpay checkout needs a browser document."));
  if (globalThis.Razorpay) return Promise.resolve();

  const existing = doc.querySelector?.('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", () => reject(new Error("Razorpay checkout failed to load.")), { once: true });
    });
  }

  return new Promise((resolve, reject) => {
    const script = doc.createElement("script");
    script.async = true;
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Razorpay checkout failed to load."));
    doc.body.appendChild(script);
  });
}
