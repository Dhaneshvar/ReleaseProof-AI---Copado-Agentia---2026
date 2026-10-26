import { proxy } from "../../../lib/proxy";
export const dynamic = "force-dynamic";
type Context = { params: { path: string[] } };
export async function GET(request: Request, context: Context) {
  return proxy(request, context.params.path.map(encodeURIComponent).join("/"));
}
export async function POST(request: Request, context: Context) {
  return proxy(request, context.params.path.map(encodeURIComponent).join("/"));
}
