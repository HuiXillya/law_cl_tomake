import json
from pathlib import Path

_DEPARTMENTS_CACHE = None


def _departments_path() -> Path:
    # project_root/src/utils -> go up three levels to project root
    return Path(__file__).resolve().parent.parent.parent / "static" / "knowledge" / "departments.json"


def load_departments() -> list:
    """Load and return the list of departments from departments.json.

    Raises FileNotFoundError or ValueError on problems (intentional: no fallback).
    """
    global _DEPARTMENTS_CACHE
    if _DEPARTMENTS_CACHE is not None:
        return _DEPARTMENTS_CACHE

    path = _departments_path()
    if not path.exists():
        raise FileNotFoundError(f"Departments file not found: {path}")

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        raise ValueError(f"Failed to read/parse departments JSON: {e}") from e

    if not isinstance(data, list):
        raise ValueError("Departments JSON must be a list of objects")

    # validate items
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Department entry at index {idx} is not an object")
        if "deptname" not in item:
            raise ValueError(f"Department entry at index {idx} missing 'deptname'")
        if "deptemail" not in item:
            raise ValueError(f"Department entry at index {idx} missing 'deptemail'")

    _DEPARTMENTS_CACHE = data
    return _DEPARTMENTS_CACHE


def get_departments() -> list:
    """Return list of department dicts (cached)."""
    return load_departments()


def get_department_names() -> list:
    """Return list of department names in the same order as JSON."""
    return [d["deptname"] for d in load_departments()]


def get_department_email(dept_name: str) -> str:
    """Return the email for the given department name. Raises KeyError if not found."""
    for d in load_departments():
        if d["deptname"] == dept_name:
            return d.get("deptemail", "")
    raise KeyError(f"Department not found: {dept_name}")
