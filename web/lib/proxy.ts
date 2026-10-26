import { NextResponse } from "next/server";

export async function proxy(request: Request, path: string) {
  const origin = request.headers.get("origin");
  if (request.method !== "GET" && origin && origin !== new URL(request.url).origin) {
    return NextResponse.json({ detail: "Origin not allowed" }, { status: 403 });
  }
  const backend = process.env.RELEASEPROOF_BACKEND_URL ?? "http://127.0.0.1:8000";
  try {
    const body = request.method === "GET" ? undefined : await request.text();
    if (body && body.length > 1_000_000) return NextResponse.json({detail: "Request too large"}, {status: 413});
    const response = await fetch(`${backend}/api/${path}${new URL(request.url).search}`, {
      method: request.method, body, headers: { "Content-Type": "application/json" },
      cache: "no-store", signal: AbortSignal.timeout(120000),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ detail: "The evidence service is unavailable. Start python server.py. No live or demo evidence was substituted." }, { status: 503 });
  }
}
