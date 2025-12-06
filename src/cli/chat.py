from __future__ import annotations

"""
CLI chat harness:
- Runs agent_root, handles delegations.
- Manages pending domain drafts; user types 'confirm' to persist (mock or real).

Public API:
- main(): REPL loop.

Usage: `./adk chat`. Honors environment flags (RUN_REAL_AI/RUN_REAL_MEMORY/RUN_REAL_DOMAINS, logging). Stores session_id across turns via ADK InMemorySessionService. Experimental: minimal UX, intended for dev/demo. See README for flags and docs/project_overview.md for flow.
"""

import sys


def main() -> None:
    print("Legacy CLI is removed. Use './adk chat' (ADK runner) instead.")
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
