import asyncio
import time
from typing import Dict, List, Optional

import aiohttp
import requests

CHAINLIST_URL = "https://chainid.network/chains.json"
DEFAULT_RPCS: Dict[int, List[str]] = {
    1: ["https://rpc.ankr.com/eth"],
    56: ["https://bsc-dataseed.binance.org/"],
    137: ["https://polygon-rpc.com"],
}

class Endpoint:
    def __init__(self, url: str):
        self.url = url
        self.latency: float = float("inf")
        self.failures: int = 0
        self.success: int = 0

    @property
    def score(self) -> float:
        return self.latency + self.failures * 5

class RPCBalancer:
    def __init__(self, chains: Optional[List[int]] = None):
        self.chains = chains or list(DEFAULT_RPCS.keys())
        self.endpoints: Dict[int, List[Endpoint]] = {}
        self.monitor_tasks: List[asyncio.Task] = []

    def load_endpoints(self) -> None:
        data = self.fetch_chainlist()
        if data is None:
            data = DEFAULT_RPCS
        for chain_id in self.chains:
            urls = data.get(chain_id, DEFAULT_RPCS.get(chain_id, []))
            self.endpoints[chain_id] = [Endpoint(u) for u in urls]

    def fetch_chainlist(self) -> Optional[Dict[int, List[str]]]:
        try:
            resp = requests.get(CHAINLIST_URL, timeout=10)
            resp.raise_for_status()
            chains = resp.json()
            mapping: Dict[int, List[str]] = {}
            for chain in chains:
                cid = chain.get("chainId")
                rpcs = chain.get("rpc", [])
                if cid is not None and rpcs:
                    mapping[cid] = rpcs
            return mapping
        except Exception:
            return None

    async def start_monitoring(self, interval: int = 15) -> None:
        for endpoints in self.endpoints.values():
            for ep in endpoints:
                task = asyncio.create_task(self.monitor_endpoint(ep, interval))
                self.monitor_tasks.append(task)

    async def monitor_endpoint(self, ep: Endpoint, interval: int) -> None:
        payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
        while True:
            start = time.perf_counter()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(ep.url, json=payload, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "result" in data:
                                ep.latency = time.perf_counter() - start
                                ep.failures = 0
                                ep.success += 1
                            else:
                                ep.failures += 1
                        else:
                            ep.failures += 1
            except Exception:
                ep.failures += 1
            await asyncio.sleep(interval)

    def get_best_endpoint(self, chain_id: int) -> Optional[str]:
        eps = self.endpoints.get(chain_id)
        if not eps:
            return None
        sorted_eps = sorted(eps, key=lambda e: e.score)
        return sorted_eps[0].url
