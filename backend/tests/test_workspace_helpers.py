from backend.routes.compare import decode_selection, encode_selection
from backend.routes.workspace import split_branch_defaults


def test_compare_history_selection_round_trips_as_ordered_codes():
    stored = encode_selection(["0001", "2006", "1315"])

    assert stored == "0001,2006,1315"
    assert decode_selection(stored) == ["0001", "2006", "1315"]


def test_workspace_branch_defaults_ignore_empty_items():
    assert split_branch_defaults("CS, IT,,EC") == ["CS", "IT", "EC"]
