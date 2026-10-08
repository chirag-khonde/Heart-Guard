#!/usr/bin/env python3
"""HeartGuard CLI health check script (Phase 16).

Used by Docker HEALTHCHECK and CI pipelines.

Exit codes:
    0  — healthy / ready
    1  — unhealthy / not ready
    2  — configuration error

Usage:
    python scripts/health_check.py [--liveness | --readiness | --full]
"""

from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path

# Ensure project root is on path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    parser = argparse.ArgumentParser(description="HeartGuard Health Check")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--liveness", action="store_true", help="Liveness check only")
    group.add_argument("--readiness", action="store_true", help="Readiness check")
    group.add_argument("--full", action="store_true", default=True, help="Full health check (default)")
    args = parser.parse_args()

    try:
        from src.health.health_service import (
            get_health_status,
            get_liveness_status,
            get_readiness_status,
        )

        if args.liveness:
            result = get_liveness_status()
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "alive" else 1

        elif args.readiness:
            result = get_readiness_status()
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "ready" else 1

        else:
            result = get_health_status()
            print(json.dumps(result, indent=2))
            if result["status"] == "healthy":
                return 0
            elif result["status"] == "degraded":
                return 1
            else:
                return 1

    except Exception as exc:
        print(json.dumps({"status": "error", "error": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
