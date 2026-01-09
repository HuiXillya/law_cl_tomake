import os
import time
import json
from typing import List, Optional
import configparser


DEFAULT_REQUIRED = [
    "config.ini",
    "static",
    "static/default.css",
    "static/main.js",
    "static/knowledge/departments.json",
]


def check_required_mounts(
    required: Optional[List[str]] = None,
    retries: int = 0,
    wait_seconds: float = 1.0,
    exit_on_missing: bool = True,
    logger=None,
) -> List[str]:
    """Simple existence check for a list of paths (backward compatible).

    This function only checks that the given paths exist. For more
    detailed department verification use `verify_departments_from_config`.
    """
    if required is None:
        required = DEFAULT_REQUIRED

    def _exists(p: str) -> bool:
        try:
            return os.path.exists(p)
        except Exception:
            return False

    missing = [p for p in required if not _exists(p)]
    attempt = 0
    while missing and attempt < retries:
        time.sleep(wait_seconds)
        missing = [p for p in required if not _exists(p)]
        attempt += 1

    if missing:
        msg = f"Missing required mounts/files: {missing}"
        if logger is not None:
            logger.error(msg)
        else:
            print(msg)
        if exit_on_missing:
            os._exit(2)

    return missing


def verify_departments_from_config(
    config_path: str = "config.ini",
    section: str = "DEPARTMENT",
    json_key: str = "department_json",
    desc_key: str = "department_description",
    exit_on_missing: bool = True,
    logger=None,
) -> None:
    """Verify config.ini -> department JSON -> Dept_description md files.

    On any missing item this function will log an error and call
    `os._exit(2)` when `exit_on_missing` is True.
    """
    def _log(msg: str):
        if logger is not None:
            logger.error(msg)
        else:
            print(msg)

    # 1) config.ini exists
    if not os.path.exists(config_path):
        _log(f"Missing config file: {config_path}")
        if exit_on_missing:
            os._exit(2)
        return

    # 2) read config.ini and locate department_json and department_description
    cfg = configparser.ConfigParser()
    try:
        cfg.read(config_path, encoding="utf-8")
    except Exception as e:
        _log(f"Failed to read config file '{config_path}': {e}")
        if exit_on_missing:
            os._exit(2)
        return

    if section not in cfg:
        _log(f"Missing section '{section}' in {config_path}")
        if exit_on_missing:
            os._exit(2)
        return

    if json_key not in cfg[section]:
        _log(f"Missing key '{json_key}' in section '{section}' of {config_path}")
        if exit_on_missing:
            os._exit(2)
        return

    dept_json_path = os.path.normpath(cfg[section][json_key])
    # allow relative paths in config
    if not os.path.isabs(dept_json_path):
        dept_json_path = os.path.join(os.getcwd(), dept_json_path)

    if not os.path.exists(dept_json_path):
        _log(f"Department JSON not found: {dept_json_path}")
        if exit_on_missing:
            os._exit(2)
        return

    # 3) parse department JSON
    try:
        raw = open(dept_json_path, encoding="utf-8").read()
        data = json.loads(raw)
    except Exception as e:
        _log(f"Failed to read/parse department JSON '{dept_json_path}': {e}")
        if exit_on_missing:
            os._exit(2)
        return

    if not isinstance(data, list):
        _log(f"Department JSON must be a list: {dept_json_path}")
        if exit_on_missing:
            os._exit(2)
        return

    # 4) find description directory
    if desc_key not in cfg[section]:
        _log(f"Missing key '{desc_key}' in section '{section}' of {config_path}")
        if exit_on_missing:
            os._exit(2)
        return

    desc_dir = os.path.normpath(cfg[section][desc_key])
    if not os.path.isabs(desc_dir):
        desc_dir = os.path.join(os.getcwd(), desc_dir)

    if not os.path.isdir(desc_dir):
        _log(f"Department description directory not found: {desc_dir}")
        if exit_on_missing:
            os._exit(2)
        return

    # 5) check each department has a corresponding .md file
    missing_files = []
    missing_emails = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict) or "deptname" not in item:
            _log(f"Invalid department entry at index {idx} in {dept_json_path}")
            if exit_on_missing:
                os._exit(2)
            return
        name = item["deptname"]

        # check deptemail exists and is non-empty
        if "deptemail" not in item or not str(item.get("deptemail") or "").strip():
            missing_emails.append(name)

        md_name = f"{name}.md"
        md_path = os.path.join(desc_dir, md_name)
        if not os.path.exists(md_path):
            missing_files.append(md_path)

    if missing_files:
        _log(f"Missing department description files: {missing_files}")
        if exit_on_missing:
            os._exit(2)

    if missing_emails:
        _log(f"Departments missing 'deptemail': {missing_emails}")
        if exit_on_missing:
            os._exit(2)
