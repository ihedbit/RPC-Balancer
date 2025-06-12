import asyncio
from typing import Any

import aiohttp
from fastapi import FastAPI, Request, Response

from .balancer import RPCBalancer

balancer = RPCBalancer()

app = FastAPI(title="RPC Proxy Balancer")

@app.on_event("startup")
async def startup_event() -> None:
    balancer.load_endpoints()
    await balancer.start_monitoring()

@app.post("/rpc/{chain_id}")
async def proxy(chain_id: int, request: Request) -> Response:
    body: Any = await request.json()
    endpoint = balancer.get_best_endpoint(chain_id)
    if not endpoint:
        return Response(status_code=404, content="Unknown chain")
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=body) as resp:
            data = await resp.read()
            headers = {k: v for k, v in resp.headers.items() if k.lower() != "content-encoding"}
            return Response(content=data, status_code=resp.status, headers=headers, media_type="application/json")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8545)
