import { type NextRequest } from "next/server";

import { cloneProxyResponseHeaders, stripHopByHopHeaders } from "@/lib/proxyHeaders";

const API_PROXY_TARGET = (process.env.API_PROXY_TARGET ?? "").trim().replace(/\/$/, "");

async function proxy(request: NextRequest, params: Promise<{ path: string[] }>) {
  if (!API_PROXY_TARGET) {
    return Response.json(
      {
        error: "API proxy is not configured",
        code: "API_PROXY_NOT_CONFIGURED",
      },
      { status: 503 },
    );
  }

  const { path } = await params;
  const pathname = path.join("/");
  const targetUrl = new URL(`${API_PROXY_TARGET}/api/${pathname}`);
  targetUrl.search = request.nextUrl.search;

  const upstreamHeaders = new Headers(request.headers);
  stripHopByHopHeaders(upstreamHeaders);
  upstreamHeaders.set("x-forwarded-host", request.headers.get("host") ?? request.nextUrl.host);
  upstreamHeaders.set("x-forwarded-proto", request.nextUrl.protocol.replace(":", ""));

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const upstreamResponse = await fetch(targetUrl, {
    method: request.method,
    headers: upstreamHeaders,
    body,
    redirect: "manual",
    cache: "no-store",
  });

  const responseHeaders = cloneProxyResponseHeaders(upstreamResponse.headers);

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context.params);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context.params);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context.params);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context.params);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context.params);
}

export async function OPTIONS(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context.params);
}
