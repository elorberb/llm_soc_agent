import copy
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


class DBManager:
    """
    Manages case and note data stored in a JSON file.
    Provides methods for note management, case status, severity, and summaries.
    """

    def __init__(self, db_path: str = "db.json") -> None:
        """
        Initialize the DBManager with the path to the database file.

        Args:
            db_path: Relative path to the JSON database file.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_path)
        self.db: List[Dict[str, Any]] = self._load_db()

    def _load_db(self) -> List[Dict[str, Any]]:
        """
        Load the database from the JSON file.

        Returns:
            List of case dictionaries.
        """
        with open(self.db_path, "r") as f:
            return json.load(f)

    def save(self) -> None:
        """
        Save the current state of the database to the JSON file.
        """
        with open(self.db_path, "w") as f:
            json.dump(self.db, f, indent=2)

    def find_case(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a case by its incident ID.

        Args:
            incident_id: The ID of the incident to find.

        Returns:
            The case dictionary if found, else None.
        """
        return next((c for c in self.db if c["IncidentID"] == incident_id), None)

    # --- Note Management ---

    def list_notes(self, incident_id: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        List all notes for a given case.

        Args:
            incident_id: The ID of the incident.

        Returns:
            List of notes, or an error dictionary if the case is not found.
        """
        case = self.find_case(incident_id)
        if not case:
            return {"error": "Case not found."}
        notes = case.get("Notes") or case.get("AdditionalNotes") or []
        return copy.deepcopy(notes)

    def add_note(
            self,
            incident_id: str,
            note: str,
            created_by: str = "SOC-User"
    ) -> Dict[str, Any]:
        """
        Add a note to a case.

        Args:
            incident_id: The ID of the incident.
            note: The note text.
            created_by: The user who created the note.

        Returns:
            Dictionary with result status and note ID, or error.
        """
        case = self.find_case(incident_id)
        if not case:
            return {"error": "Case not found."}
        notes = case.setdefault("Notes", [])
        next_id = max([n["NoteId"] for n in notes] or [0]) + 1
        notes.append({
            "NoteId": next_id,
            "Note": note,
            "CreatedBy": created_by,
            "Time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        })
        return {"ok": True, "note_id": next_id}

    def remove_note(self, incident_id: str, note_id: int) -> Dict[str, Any]:
        """
        Remove a note by its ID from a case.

        Args:
            incident_id: The ID of the incident.
            note_id: The ID of the note to remove.

        Returns:
            Dictionary with result status or error.
        """
        case = self.find_case(incident_id)
        if not case:
            return {"error": "Case not found."}
        notes = case.setdefault("Notes", [])
        filtered = [n for n in notes if n["NoteId"] != note_id]
        if len(filtered) == len(notes):
            return {"error": "Note not found."}
        case["Notes"] = filtered
        return {"ok": True}

    def edit_note(self, incident_id: str, note_id: int, new_text: str) -> Dict[str, Any]:
        """
        Edit the text of a note by its ID.

        Args:
            incident_id: The ID of the incident.
            note_id: The ID of the note to edit.
            new_text: The new note text.

        Returns:
            Dictionary with result status or error.
        """
        case = self.find_case(incident_id)
        if not case:
            return {"error": "Case not found."}
        notes = case.setdefault("Notes", [])
        for n in notes:
            if n["NoteId"] == note_id:
                n["Note"] = new_text
                return {"ok": True}
        return {"error": "Note not found."}

    # --- Change Case State ---

    def set_status(self, incident_id: str, status: str) -> Dict[str, Any]:
        """
        Set the status of a case (open or closed).

        Args:
            incident_id: The ID of the incident.
            status: The new status ("open" or "closed").

        Returns:
            Dictionary with result status or error.
        """
        status = status.lower()
        assert status.lower() in ("open", "closed")
        case = self.find_case(incident_id)
        if not case:
            return {"error": "Case not found."}
        case["CaseStatus"] = status
        return {"ok": True}

    # --- Update Case Severity ---

    def set_severity(self, incident_id: str, severity: str) -> Dict[str, Any]:
        """
        Set the severity level of a case.

        Args:
            incident_id: The ID of the incident.
            severity: The new severity ("Low", "Medium", "High", "Critical").

        Returns:
            Dictionary with result status or error.
        """
        severity = severity.capitalize()  # Normalize to title case
        assert severity in ("Low", "Medium", "High", "Critical")
        case = self.find_case(incident_id)
        if not case:
            return {"error": "Case not found."}
        case["SeverityLevel"] = severity
        return {"ok": True}

    # --- Summaries ---

    def list_open_cases(self) -> List[Dict[str, Any]]:
        """
        List all currently open cases.

        Returns:
            List of open case dictionaries.
        """
        return [c for c in self.db if c.get("CaseStatus") == "Open"]

    # --- Add new Case ---
    def create_case(
            self,
            incident_id: str,
            description: str,
            incident_type: str,
            severity: str,
            status: str
    ) -> Dict[str, Any]:
        """
        Create and append a new case to the database.

        Args:
            incident_id: Unique ID for the new incident.
            description: Description of the incident.
            incident_type: Type of the incident (e.g., "Phishing Attack", "EDR").
            severity: Severity level ("Low", "Medium", "High", "Critical").
            status: Case status ("Open" or "Closed").

        Returns:
            Dictionary with result status or error.
        """
        if self.find_case(incident_id):
            return {"error": f"Incident ID '{incident_id}' already exists."}

        case = {
            "IncidentID": incident_id,
            "CaseDescription": description,
            "IncidentType": incident_type,
            "SeverityLevel": severity.capitalize(),
            "CaseStatus": status.capitalize(),
            "Notes": []
        }
        self.db.append(case)
        self.save()
        return {"ok": True, "incident_id": incident_id}
