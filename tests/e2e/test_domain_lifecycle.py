import sys
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))
os.environ.setdefault("RUN_REAL_DOMAINS", "0")
os.environ["ENABLE_GCP_LOGGING"] = "0"
os.environ.setdefault("RUN_REAL_AI", "0")


def test_domain_lifecycle_draft_and_confirm():
    from src.agents.subagent_domain_lifecycle import run_subagent_domain_lifecycle
    session_id = "sess_e2e_domain"
    state = {"user_id": "user_1"}

    first_turn = run_subagent_domain_lifecycle(
        {
            "operation_type": "CREATE",
            "user_input": "Track AI research",
            "confirmation_status": False,
            "session_id": session_id,
        },
        session_id=session_id,
        session_state=state,
    )
    assert first_turn["status"] == "AWAITING_USER_REVIEW"
    draft = first_turn["domain_draft"]
    assert draft["name"]

    state.update(first_turn.get("state_delta", {}))

    second_turn = run_subagent_domain_lifecycle(
        {
            "operation_type": "CREATE",
            "user_input": "Track AI research",
            "confirmation_status": True,
            "domain_id": draft["domain_id"],
            "session_id": session_id,
        },
        session_id=session_id,
        session_state=state,
    )
    assert second_turn["status"] == "SUCCESS"
    assert second_turn["domain_draft"]["domain_id"] == draft["domain_id"]
    assert "saved" in second_turn["message_to_user"].lower()
