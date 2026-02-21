from fastapi import FastAPI, HTTPException, Request, Response
import httpx

app = FastAPI(title="K-Card API Gateway", version="0.1.0")

SERVICE_MAP = {
    "auth": "http://auth-service:8001",
    "wallets": "http://wallet-service:8002",
    "payments": "http://payments-service:8003",
    "merchants": "http://transport-service:8004",
    "vehicles": "http://transport-service:8004",
    "cabs": "http://transport-service:8004",
    "rides": "http://transport-service:8004",
    "payouts": "http://payout-service:8005",
    "credit": "http://credit-service:8006",
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request) -> Response:
    prefix = path.split("/")[0]
    base = SERVICE_MAP.get(prefix)
    if not base:
        raise HTTPException(status_code=404, detail="Unknown API route")
    target = f"{base}/api/v1/{path}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        upstream = await client.request(request.method, target, params=request.query_params, content=body, headers=headers)
    return Response(content=upstream.content, status_code=upstream.status_code, headers=dict(upstream.headers))
