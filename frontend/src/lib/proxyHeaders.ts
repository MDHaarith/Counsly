export function stripHopByHopHeaders(headers: Headers) {
  headers.delete("connection");
  headers.delete("content-length");
  headers.delete("host");
  headers.delete("transfer-encoding");
}

export function cloneProxyResponseHeaders(upstreamHeaders: Headers): Headers {
  const responseHeaders = new Headers();

  for (const [name, value] of upstreamHeaders.entries()) {
    if (name.toLowerCase() === "set-cookie") {
      continue;
    }
    responseHeaders.set(name, value);
  }

  const getSetCookie = (upstreamHeaders as Headers & { getSetCookie?: () => string[] }).getSetCookie;
  if (typeof getSetCookie === "function") {
    for (const cookie of getSetCookie.call(upstreamHeaders)) {
      responseHeaders.append("set-cookie", cookie);
    }
  } else {
    const setCookie = upstreamHeaders.get("set-cookie");
    if (setCookie) {
      responseHeaders.append("set-cookie", setCookie);
    }
  }

  stripHopByHopHeaders(responseHeaders);
  return responseHeaders;
}
