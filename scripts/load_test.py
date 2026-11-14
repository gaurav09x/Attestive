"""Small concurrent load check for read-only endpoints.

Usage:
    python scripts/load_test.py --requests 200 --concurrency 20
    python scripts/load_test.py --base-url http://localhost:8000

It reports latency percentiles and non-2xx responses. It is a smoke check for a
single process, not a substitute for a production load test with realistic data.
"""

from __future__ import annotations

import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import httpx

ENDPOINTS = ("/api/v1/health", "/api/v1/catalog/subjects")


@dataclass
class Result:
    status: int
    milliseconds: float


def percentile(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((value / 100) * len(ordered) + 0.5)) - 1))
    return ordered[index]


def run_endpoint(base_url: str, path: str, requests: int, concurrency: int) -> list[Result]:
    url = f"{base_url.rstrip('/')}{path}"

    # One pooled client: creating a connection per request measures TCP setup on
    # Windows, not the API (hundreds of ms versus a few ms with keep-alive).
    with httpx.Client(timeout=15) as client:

        def one(_: int) -> Result:
            started = time.perf_counter()
            try:
                status = client.get(url).status_code
            except httpx.HTTPError:
                status = 0
            return Result(status=status, milliseconds=(time.perf_counter() - started) * 1000)

        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            return list(pool.map(one, range(requests)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Concurrent read-endpoint load check")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    print(
        f"Load check: {args.requests} requests per endpoint, "
        f"concurrency {args.concurrency}, base {args.base_url}"
    )
    print(
        f"{'endpoint':<28}{'ok':>6}{'429':>6}{'fail':>6}"
        f"{'p50 ms':>9}{'p95 ms':>9}{'p99 ms':>9}{'mean':>9}"
    )

    failures = 0
    for path in ENDPOINTS:
        results = run_endpoint(args.base_url, path, args.requests, args.concurrency)
        # Rejected requests are fast and would distort percentiles; report them
        # separately because the API throttles above the configured budget.
        accepted = [item for item in results if item.status != 429]
        durations = [item.milliseconds for item in accepted]
        ok = sum(1 for item in results if 200 <= item.status < 300)
        limited = sum(1 for item in results if item.status == 429)
        failed = len(results) - ok - limited
        failures += failed
        print(
            f"{path:<28}{ok:>6}{limited:>6}{failed:>6}"
            f"{percentile(durations, 50):>9.1f}{percentile(durations, 95):>9.1f}"
            f"{percentile(durations, 99):>9.1f}{statistics.fmean(durations):>9.1f}"
        )

    if failures:
        print(f"{failures} request(s) did not return 2xx. Inspect the API log.")
    print(
        "Note: 429s are the rate limiter, not errors. Keep --requests below the "
        "per-minute budget to measure latency under load."
    )


if __name__ == "__main__":
    main()
