import hashlib
import time
from typing import Dict, Any, Optional

class SemanticCache:
    """
    In-Memory Semantic Cache for LLM Prompt Deduplication & Latency Optimization.
    Delivers instant sub-2ms cache hits for identical or normalized prompts.
    """
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _normalize_key(self, prompt: str, system_prompt: str = "") -> str:
        raw = f"{system_prompt.strip()}||{prompt.strip()}".lower()
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def get(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        key = self._normalize_key(prompt, system_prompt)
        entry = self.cache.get(key)
        if entry:
            # Check TTL
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                self.hits += 1
                return entry["response"]
            else:
                del self.cache[key]
        self.misses += 1
        return None

    def set(self, prompt: str, response: str, system_prompt: str = ""):
        if len(self.cache) >= self.max_size:
            # LRU style eviction: delete oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        key = self._normalize_key(prompt, system_prompt)
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = round((self.hits / total * 100), 1) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_pct": f"{hit_rate}%",
            "cached_entries": len(self.cache),
            "estimated_latency_saved_ms": self.hits * 1250,
            "estimated_cost_saved_usd": round(self.hits * 0.0025, 4)
        }

# Global Singleton
semantic_cache = SemanticCache()
