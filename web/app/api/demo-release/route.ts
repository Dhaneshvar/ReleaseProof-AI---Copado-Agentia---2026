import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";
export async function GET() {
  return NextResponse.json({detail: "Create an explicit demo analysis with POST /api/analyze. No fallback evidence is returned."}, {status: 410});
}

