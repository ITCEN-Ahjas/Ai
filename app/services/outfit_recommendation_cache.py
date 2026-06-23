from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Literal, Mapping

from app.schemas.outfit_batch_request import OutfitBatchRecommendationRequest
from app.schemas.outfit_response import OutfitSelection


@dataclass(frozen=True)
class CachedBatchRecommendation:
    source: Literal["ai", "fallback"]
    selections: dict[str, OutfitSelection]
    expires_at: float


class OutfitRecommendationCache:
    def __init__(
        self,
        ttl_seconds: int = 600,
        failure_retry_seconds: int = 300,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("캐시 유지 시간은 0보다 커야 합니다.")

        if failure_retry_seconds <= 0:
            raise ValueError("실패 재시도 대기 시간은 0보다 커야 합니다.")

        self._ttl_seconds = ttl_seconds
        self._failure_retry_seconds = failure_retry_seconds
        self._entries: dict[str, CachedBatchRecommendation] = {}
        self._warming_keys: set[str] = set()
        self._retry_after: dict[str, float] = {}
        self._lock = threading.RLock()

    def create_key(
        self,
        request: OutfitBatchRecommendationRequest,
    ) -> str:
        payload = json.dumps(
            request.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(
        self,
        cache_key: str,
    ) -> CachedBatchRecommendation | None:
        with self._lock:
            self._prune_expired_locked()

            entry = self._entries.get(cache_key)

            if entry is None:
                return None

            return CachedBatchRecommendation(
                source=entry.source,
                selections=self._copy_selections(entry.selections),
                expires_at=entry.expires_at,
            )

    def save(
        self,
        cache_key: str,
        *,
        source: Literal["ai", "fallback"],
        selections: Mapping[str, OutfitSelection],
    ) -> None:
        with self._lock:
            self._entries[cache_key] = CachedBatchRecommendation(
                source=source,
                selections=self._copy_selections(selections),
                expires_at=time.monotonic() + self._ttl_seconds,
            )

    def reserve_warmup(
        self,
        cache_key: str,
    ) -> bool:
        with self._lock:
            self._prune_expired_locked()

            entry = self._entries.get(cache_key)

            if entry is not None and entry.source == "ai":
                return False

            if cache_key in self._warming_keys:
                return False

            retry_after = self._retry_after.get(cache_key)

            if retry_after is not None and retry_after > time.monotonic():
                return False

            self._warming_keys.add(cache_key)

            return True

    def complete_warmup(
        self,
        cache_key: str,
        *,
        succeeded: bool,
    ) -> None:
        with self._lock:
            self._warming_keys.discard(cache_key)

            if succeeded:
                self._retry_after.pop(cache_key, None)
                return

            self._retry_after[cache_key] = (
                time.monotonic() + self._failure_retry_seconds
            )

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._warming_keys.clear()
            self._retry_after.clear()

    def _prune_expired_locked(self) -> None:
        now = time.monotonic()

        expired_keys = [
            cache_key
            for cache_key, entry in self._entries.items()
            if entry.expires_at <= now
        ]

        for cache_key in expired_keys:
            self._entries.pop(cache_key, None)

        retry_expired_keys = [
            cache_key
            for cache_key, retry_after in self._retry_after.items()
            if retry_after <= now
        ]

        for cache_key in retry_expired_keys:
            self._retry_after.pop(cache_key, None)

    def _copy_selections(
        self,
        selections: Mapping[str, OutfitSelection],
    ) -> dict[str, OutfitSelection]:
        return {
            travel_style: selection.model_copy(deep=True)
            for travel_style, selection in selections.items()
        }