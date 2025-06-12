# RPC Proxy Balancer

This project provides a lightweight HTTP JSON-RPC proxy that automatically fetches RPC endpoints for various EVM compatible chains from [Chainlist](https://chainlist.org). It monitors the health of the available endpoints and forwards requests to the node with the best recent performance.

## Features

- **Automatic endpoint discovery** using `https://chainid.network/chains.json`.
- **Health monitoring** of RPC endpoints by calling `eth_blockNumber` periodically.
- **Smart routing** that selects the fastest endpoint with the fewest recent failures.
- **Fallback** to a built-in list of RPC URLs if Chainlist cannot be reached.
- **Simple HTTP interface** using FastAPI. Send JSON-RPC requests to `/rpc/<chain_id>`.

## Requirements

- Python 3.8+
- `fastapi`, `uvicorn`, `aiohttp`, `requests`

Install dependencies with:

```bash
pip install fastapi uvicorn aiohttp requests
```

## Running the Proxy

```bash
python -m rpc_balancer.server
```

The server listens on port `8545` by default. Example request:

```bash
curl -X POST http://localhost:8545/rpc/1 -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

## Notes

- When the server starts, it fetches data from Chainlist. If the request fails, the proxy uses a minimal built-in list of RPC endpoints.
- Health checks run every 15 seconds per endpoint and update the latency and error counters used to pick the best node.
