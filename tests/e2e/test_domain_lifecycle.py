import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


def test_domain_lifecycle_draft_and_confirm():
    from src.agents.subagent_domain_lifecycle import run_subagent_domain_lifecycle

    first_turn = run_subagent_domain_lifecycle(
        {
            "operation_type": "CREATE",
            "user_id": "user_1",
            "user_input": "Track AI research",
            "confirmation_status": False,
        }
    )
    assert first_turn["status"] == "AWAITING_USER_REVIEW"
    draft = first_turn["domain_draft"]
    assert draft["name"]

    second_turn = run_subagent_domain_lifecycle(
        {
            "operation_type": "CREATE",
            "user_id": "user_1",
            "user_input": "Track AI research",
            "confirmation_status": True,
            "domain_id": draft["domain_id"],
        }
    )
    assert second_turn["status"] == "SUCCESS"
    assert second_turn["domain_draft"]["domain_id"] == draft["domain_id"]
    assert "saved" in second_turn["message_to_user"].lower()
