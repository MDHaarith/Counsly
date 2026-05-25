const paidScreens = new Set(["/choices", "/analytics", "/rounds"]);

export function paidFeatureDestination(pathname) {
  if (!paidScreens.has(pathname)) return "";
  return `/subscribe?from=${pathname.slice(1)}`;
}

export function choiceWriteDestination(user, source = "choices") {
  if (user?.subscription_active) return "";
  return `/subscribe?from=${encodeURIComponent(source)}`;
}
