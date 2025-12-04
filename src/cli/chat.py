from __future__ import annotations

"""
CLI chat harness:
- Runs agent_root, handles delegations.
- Manages pending domain drafts; user types 'confirm' to persist (mock or real).

Public API:
- main(): REPL loop.

Usage: `./adk chat`. Honors environment flags (RUN_REAL_AI/RUN_REAL_MEMORY/RUN_REAL_DOMAINS, logging). Stores session_user_id across turns. Experimental: minimal UX, intended for dev/demo. See README for flags and docs/project_overview.md for flow.
"""

import json
import sys
from typing import Optional

from src.agents.agent_root import run_agent_root
from src.agents.subagent_document_processor import run_subagent_document_processor
from src.agents.subagent_domain_lifecycle import run_subagent_domain_lifecycle


def main() -> None:
    session_user_id: Optional[str] = None
    pending_domain_state: Optional[dict] = None
    name_attempts = 0
    # Agent initiates greeting
    initial = run_agent_root("", session_user_id=session_user_id, name_attempts=name_attempts)
    if initial.get("response_message"):
        print(f"[root] {json.dumps(initial, ensure_ascii=False)}")
    print("CLI chat. Type 'exit' to quit.")
    while True:
        try:
            user_input = input("> ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        # Handle pending domain confirmation locally.
        if pending_domain_state and user_input.lower() in {"confirm", "yes", "y"}:
            payload = {
                "operation_type": pending_domain_state.get("operation_type", "CREATE"),
                "user_id": pending_domain_state["user_id"],
                "user_input": pending_domain_state["user_input"],
                "confirmation_status": True,
                "domain_id": pending_domain_state["domain_draft"].get("domain_id"),
            }
            sub_res = run_subagent_domain_lifecycle(payload)
            print(f"[subagent_domain_lifecycle] {json.dumps(sub_res, ensure_ascii=False)}")
            pending_domain_state = None
            if sub_res.get("status") == "SUCCESS":
                print("[info] Domain saved; continuing.")
            continue

        if session_user_id is None:
            name_attempts += 1
        root_res = run_agent_root(user_input, session_user_id=session_user_id, name_attempts=name_attempts)
        print(f"[root] {json.dumps(root_res, ensure_ascii=False)}")
        if root_res.get("authenticated_user_id"):
            session_user_id = root_res["authenticated_user_id"]
            name_attempts = 0
        if root_res.get("status") == "DELEGATE":
            target = root_res.get("delegation_target")
            payload = root_res.get("delegation_payload", {})
            if target == "subagent_document_processor":
                sub_res = run_subagent_document_processor(payload)
                print(f"[subagent_document_processor] {json.dumps(sub_res, ensure_ascii=False)}")
            elif target == "subagent_domain_lifecycle":
                sub_res = run_subagent_domain_lifecycle(payload)
                print(f"[subagent_domain_lifecycle] {json.dumps(sub_res, ensure_ascii=False)}")
                if sub_res.get("status") == "AWAITING_USER_REVIEW" and "domain_draft" in sub_res:
                    pending_domain_state = {
                        "domain_draft": sub_res["domain_draft"],
                        "operation_type": payload.get("operation_type", "CREATE"),
                        "user_id": payload.get("user_id"),
                        "user_input": payload.get("user_input", ""),
                    }
                    print("[info] Pending draft stored; reply 'confirm' to save.")
    print("Goodbye.")


if __name__ == "__main__":
    sys.exit(main())
