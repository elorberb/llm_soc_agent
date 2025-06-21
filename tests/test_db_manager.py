import pytest

from core.db_manager import DBManager


@pytest.fixture
def mock_manager(tmp_path):
    test_db_path = tmp_path / "test_db.json"

    # Sample test data, you could also load from a file if preferred
    test_data = [
        {
            "IncidentID": "INC-1",
            "CaseStatus": "Open",
            "SeverityLevel": "High",
            "Notes": [
                {"NoteId": 1, "Note": "First note", "CreatedBy": "Tester", "Time": "2025-01-01 00:00 UTC"}
            ]
        }
    ]

    # Save to temp file
    test_db_path.write_text(json_dump(test_data))

    # Load into manager
    manager = DBManager(str(test_db_path))
    return manager


def json_dump(data):
    import json
    return json.dumps(data, indent=2)


# --- Note Management Tests ---

def test_list_notes_found(mock_manager):
    notes = mock_manager.list_notes("INC-1")
    assert isinstance(notes, list)
    assert notes[0]["Note"] == "First note"


def test_list_notes_not_found(mock_manager):
    result = mock_manager.list_notes("INC-404")
    assert "error" in result


def test_add_note(mock_manager):
    result = mock_manager.add_note("INC-1", "A new note", created_by="UnitTest")
    assert result["ok"]
    notes = mock_manager.list_notes("INC-1")
    assert any(n["Note"] == "A new note" for n in notes)


def test_add_note_case_not_found(mock_manager):
    result = mock_manager.add_note("INC-404", "Should fail")
    assert "error" in result


def test_remove_note_success(mock_manager):
    add_result = mock_manager.add_note("INC-1", "To be removed")
    note_id = add_result["note_id"]
    result = mock_manager.remove_note("INC-1", note_id)
    assert result["ok"]
    notes = mock_manager.list_notes("INC-1")
    assert all(n["NoteId"] != note_id for n in notes)


def test_remove_note_not_found(mock_manager):
    result = mock_manager.remove_note("INC-1", 999)
    assert "error" in result


def test_remove_note_case_not_found(mock_manager):
    result = mock_manager.remove_note("INC-404", 1)
    assert "error" in result


def test_edit_note_success(mock_manager):
    mock_manager.add_note("INC-1", "Edit me")
    notes = mock_manager.list_notes("INC-1")
    note_id = notes[-1]["NoteId"]
    result = mock_manager.edit_note("INC-1", note_id, "Edited text")
    assert result["ok"]
    notes = mock_manager.list_notes("INC-1")
    assert any(n["Note"] == "Edited text" for n in notes)


def test_edit_note_not_found(mock_manager):
    result = mock_manager.edit_note("INC-1", 999, "No such note")
    assert "error" in result


def test_edit_note_case_not_found(mock_manager):
    result = mock_manager.edit_note("INC-404", 1, "No such case")
    assert "error" in result


# --- Change Case State Tests ---

def test_set_status_success(mock_manager):
    result = mock_manager.set_status("INC-1", "Closed")
    assert result["ok"]
    case = mock_manager.find_case("INC-1")
    assert case["CaseStatus"] == "Closed"


def test_set_status_case_not_found(mock_manager):
    result = mock_manager.set_status("INC-404", "Open")
    assert "error" in result


# --- Update Case Severity Tests ---

def test_set_severity_success(mock_manager):
    result = mock_manager.set_severity("INC-1", "Low")
    assert result["ok"]
    case = mock_manager.find_case("INC-1")
    assert case["SeverityLevel"] == "Low"


def test_set_severity_case_not_found(mock_manager):
    result = mock_manager.set_severity("INC-404", "High")
    assert "error" in result


# --- Summaries Tests ---

def test_get_open_cases(mock_manager):
    open_cases = mock_manager.list_open_cases()
    assert isinstance(open_cases, list)
    assert open_cases[0]["IncidentID"] == "INC-1"
    assert open_cases[0]["CaseStatus"] == "Open"


# --- Create new case Tests ---

def test_create_case(mock_manager):
    result = mock_manager.create_case(
        incident_id="INC-TEST",
        description="Test incident description",
        incident_type="Malware",
        severity="Medium",
        status="Open"
    )
    assert result["ok"]
    assert result["incident_id"] == "INC-TEST"

    # Verify case was created
    case = mock_manager.find_case("INC-TEST")
    assert case is not None
    assert case["IncidentID"] == "INC-TEST"
    assert case["CaseDescription"] == "Test incident description"
    assert case["IncidentType"] == "Malware"
    assert case["SeverityLevel"] == "Medium"
    assert case["CaseStatus"] == "Open"
    assert case["Notes"] == []


def test_create_case_duplicate_id(mock_manager):
    # Add first case
    mock_manager.create_case("INC-DUP", "First case", "Phishing", "Low", "Open")

    # Try to add case with same ID
    result = mock_manager.create_case("INC-DUP", "Second case", "Malware", "High", "Open")
    assert "error" in result
