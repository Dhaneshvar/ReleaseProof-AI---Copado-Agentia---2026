"""FastAPI transport; all behavior lives in the shared ReleaseService."""
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .api import dispatch
from .engine import ReleaseService

app = FastAPI(title="ReleaseProof AI", version="0.3.0")
service = ReleaseService(recover=True)


@app.api_route("/api/{path:path}", methods=["GET", "POST"])
async def api(path: str, request: Request):
    origin = request.headers.get("origin")
    if origin and origin not in {"http://localhost:3000", "http://127.0.0.1:3000"}:
        return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
    if int(request.headers.get("content-length", "0")) > 1_000_000:
        return JSONResponse({"detail": "Request too large"}, status_code=413)
    try:
        raw = await request.body()
        if len(raw) > 1_000_000:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
        body = json.loads(raw) if raw else {}
        if not isinstance(body, dict):
            raise ValueError("Expected a JSON object")
        from starlette.concurrency import run_in_threadpool
        result = await run_in_threadpool(dispatch, service, request.method, str(request.url.path) + ("?" + request.url.query if request.url.query else ""), body)
        return JSONResponse(result, headers={"Cache-Control": "no-store"})
    except KeyError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=404)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400)
    except Exception:
        return JSONResponse({"detail": "Evidence service failed. No passing evidence was generated."}, status_code=500)

