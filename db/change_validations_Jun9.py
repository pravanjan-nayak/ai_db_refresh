import os
import re
import shutil
from typing import Dict, Any, List


def _normalize_tablespace_name(name: str) -> str:
    return (name or "").strip().upper()


def _gb_from_bytes(value: int) -> float:
    return round(value / (1024 ** 3), 2)


def get_tablespace_contents(conn, tablespace_name: str) -> str:
    """
    Returns tablespace contents type: PERMANENT / TEMPORARY / UNDO
    """
    ts = _normalize_tablespace_name(tablespace_name)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT contents
        FROM dba_tablespaces
        WHERE tablespace_name = :ts
        """,
        {"ts": ts}
    )
    row = cursor.fetchone()
    cursor.close()

    if not row:
        return ""

    return str(row[0]).upper()


def get_tablespace_datafiles(conn, tablespace_name: str) -> List[Dict[str, Any]]:
    """
    Read current datafiles for a permanent tablespace.
    """
    ts = _normalize_tablespace_name(tablespace_name)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT file_name, bytes
        FROM dba_data_files
        WHERE tablespace_name = :ts
        ORDER BY file_name
        """,
        {"ts": ts}
    )
    rows = cursor.fetchall()
    cursor.close()

    results = []
    for row in rows:
        results.append({
            "file_name": row[0],
            "bytes": int(row[1]),
            "size_gb": _gb_from_bytes(int(row[1]))
        })
    return results


def detect_storage_type(file_path: str) -> str:
    """
    For now we mainly support filesystem.
    Still keeping basic detection for future use.
    """
    if not file_path:
        return "UNKNOWN"

    if file_path.startswith("+"):
        return "ASM"

    return "FILESYSTEM"


def get_directory_from_file_path(file_path: str) -> str:
    """
    Works for Windows-style filesystem paths.
    """
    if not file_path:
        return ""
    return os.path.dirname(file_path)


def get_drive_root_from_path(path_value: str) -> str:
    """
    Example:
    D:\\oracle\\oradata\\ORCL\\users01.dbf  -> D:\\
    """
    if not path_value:
        return ""

    drive, _ = os.path.splitdrive(path_value)
    if not drive:
        return ""

    return drive + "\\"


def get_windows_drive_space_gb(path_value: str) -> Dict[str, float]:
    """
    Checks total/used/free space for the Windows drive where the file path exists.
    """
    drive_root = get_drive_root_from_path(path_value)
    if not drive_root:
        raise ValueError(f"Could not determine Windows drive from path: {path_value}")

    total, used, free = shutil.disk_usage(drive_root)

    return {
        "drive_root": drive_root,
        "total_gb": _gb_from_bytes(total),
        "used_gb": _gb_from_bytes(used),
        "free_gb": _gb_from_bytes(free)
    }


def generate_next_datafile_name(existing_files: List[str], tablespace_name: str) -> str:
    """
    Generate next filename using the directory naming pattern.
    Examples:
        users_01.dbf -> users_02.dbf
        users01.dbf  -> users02.dbf
        otherwise    -> users_01.dbf
    """
    base_ts = _normalize_tablespace_name(tablespace_name).lower()

    if not existing_files:
        return f"{base_ts}_01.dbf"

    last_file = os.path.basename(existing_files[-1])

    patterns = [
        r"^(.*?)(\d+)(\.dbf)$",         # users01.dbf
        r"^(.*?[_-])(\d+)(\.dbf)$"      # users_01.dbf / users-01.dbf
    ]

    for pattern in patterns:
        match = re.match(pattern, last_file, re.IGNORECASE)
        if match:
            prefix = match.group(1)
            number = match.group(2)
            ext = match.group(3)
            next_num = int(number) + 1
            return f"{prefix}{str(next_num).zfill(len(number))}{ext}"

    return f"{base_ts}_01.dbf"


def build_statement_preview(
    tablespace_name: str,
    file_path: str,
    requested_size_gb: int,
    autoextend: bool = True,
    next_gb: int = 1,
    maxsize_gb: int = 20
) -> str:
    ts = _normalize_tablespace_name(tablespace_name)

    statement = (
        f"ALTER TABLESPACE {ts} "
        f"ADD DATAFILE '{file_path}' "
        f"SIZE {requested_size_gb}G "
    )

    if autoextend:
        statement += f"AUTOEXTEND ON NEXT {next_gb}G MAXSIZE {maxsize_gb}G"
    else:
        statement += "AUTOEXTEND OFF"

    return statement


def recommend_add_datafile(
    conn,
    tablespace_name: str,
    requested_size_gb: int,
    safety_buffer_gb: int = 2,
    autoextend: bool = True,
    next_gb: int = 1,
    maxsize_gb: int = 20
) -> Dict[str, Any]:
    """
    Main read-only function:
    - checks tablespace
    - reads current datafiles
    - derives recommended directory
    - checks Windows drive free space
    - prepares statement preview
    """
    ts = _normalize_tablespace_name(tablespace_name)

    result = {
        "valid": False,
        "tablespace_name": ts,
        "requested_size_gb": requested_size_gb,
        "safety_buffer_gb": safety_buffer_gb,
        "checks": [],
        "existing_files": [],
        "storage_type": "UNKNOWN",
        "recommended_directory": "",
        "recommended_file_name": "",
        "recommended_file_path": "",
        "drive_space": {},
        "sufficient_space": False,
        "statement_preview": "",
        "errors": []
    }

    if not ts:
        result["errors"].append("Tablespace name is empty.")
        return result

    if not isinstance(requested_size_gb, int) or requested_size_gb <= 0:
        result["errors"].append("requested_size_gb must be a positive integer.")
        return result

    contents = get_tablespace_contents(conn, ts)
    if not contents:
        result["checks"].append({
            "name": "tablespace_exists",
            "status": "FAIL",
            "details": f"Tablespace {ts} not found."
        })
        result["errors"].append(f"Tablespace {ts} not found.")
        return result

    result["checks"].append({
        "name": "tablespace_exists",
        "status": "PASS",
        "details": f"Tablespace {ts} exists."
    })

    result["checks"].append({
        "name": "tablespace_contents",
        "status": "PASS" if contents == "PERMANENT" else "FAIL",
        "details": f"Contents type = {contents}"
    })

    if contents != "PERMANENT":
        result["errors"].append(
            f"Add datafile step currently supports only PERMANENT tablespaces. Found: {contents}"
        )
        return result

    datafiles = get_tablespace_datafiles(conn, ts)
    if not datafiles:
        result["checks"].append({
            "name": "existing_datafiles",
            "status": "FAIL",
            "details": f"No existing datafiles found for tablespace {ts}."
        })
        result["errors"].append(f"No existing datafiles found for tablespace {ts}.")
        return result

    result["checks"].append({
        "name": "existing_datafiles",
        "status": "PASS",
        "details": f"Found {len(datafiles)} existing datafile(s)."
    })

    existing_files = [item["file_name"] for item in datafiles]
    result["existing_files"] = existing_files

    first_file = existing_files[0]
    storage_type = detect_storage_type(first_file)
    result["storage_type"] = storage_type

    result["checks"].append({
        "name": "storage_type",
        "status": "PASS" if storage_type == "FILESYSTEM" else "FAIL",
        "details": f"Detected storage type = {storage_type}"
    })

    if storage_type != "FILESYSTEM":
        result["errors"].append(
            f"Current step supports FILESYSTEM only. Detected: {storage_type}"
        )
        return result

    recommended_directory = get_directory_from_file_path(existing_files[-1])
    result["recommended_directory"] = recommended_directory

    if not os.path.isdir(recommended_directory):
        result["checks"].append({
            "name": "directory_exists",
            "status": "FAIL",
            "details": f"Directory does not exist on server: {recommended_directory}"
        })
        result["errors"].append(
            f"Directory does not exist on server: {recommended_directory}"
        )
        return result

    result["checks"].append({
        "name": "directory_exists",
        "status": "PASS",
        "details": f"Directory exists: {recommended_directory}"
    })

    recommended_file_name = generate_next_datafile_name(existing_files, ts)
    recommended_file_path = os.path.join(recommended_directory, recommended_file_name)

    result["recommended_file_name"] = recommended_file_name
    result["recommended_file_path"] = recommended_file_path

    drive_space = get_windows_drive_space_gb(recommended_file_path)
    result["drive_space"] = drive_space

    required_gb = requested_size_gb + safety_buffer_gb
    sufficient_space = drive_space["free_gb"] >= required_gb
    result["sufficient_space"] = sufficient_space

    result["checks"].append({
        "name": "free_space_check",
        "status": "PASS" if sufficient_space else "FAIL",
        "details": (
            f"Free space on {drive_space['drive_root']} = {drive_space['free_gb']} GB; "
            f"required = {required_gb} GB "
            f"(requested {requested_size_gb} GB + buffer {safety_buffer_gb} GB)"
        )
    })

    if not sufficient_space:
        result["errors"].append(
            f"Insufficient disk space. Free={drive_space['free_gb']} GB, required={required_gb} GB."
        )
        return result

    statement_preview = build_statement_preview(
        tablespace_name=ts,
        file_path=recommended_file_path,
        requested_size_gb=requested_size_gb,
        autoextend=autoextend,
        next_gb=next_gb,
        maxsize_gb=maxsize_gb
    )

    result["statement_preview"] = statement_preview
    result["valid"] = True

    return result