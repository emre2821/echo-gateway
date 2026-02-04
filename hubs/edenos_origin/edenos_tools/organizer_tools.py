# organizer_tools.py

# Safe, permission-gated organizer tools for EdenOS
# Provides a persistent, revocable permission model stored in
# tools/permissions.json. All read/write/move/rename operations
# must be requested and then explicitly granted (by a human).

from . import eden_tool, TextContent, JsonContent
import os
import shutil
import json
import uuid
import time

# permissions file lives next to this module
PERMISSIONS_FILE = os.path.join(os.path.dirname(__file__), "permissions.json")


def _load_permissions():
    try:
        with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"permissions": {}, "requests": {}}
    return data


def _save_permissions(data):
    with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _audit(event_type: str, details: dict):
    """Append an audit entry to the permissions store."""
    data = _load_permissions()
    entry = {
        "id": _make_id(),
        "event": event_type,
        "details": details,
        "ts": time.time(),
    }
    data.setdefault("audit", []).append(entry)
    _save_permissions(data)


# -------------------------------------------------------------
# 1) HARD EXCLUSION ZONES (Windows core + user-protected folders)
# -------------------------------------------------------------
EXCLUSION_ZONES = [
    r"C:\\Windows",
    r"C:\\Program Files",
    r"C:\\Program Files (x86)",
    r"C:\\Users\\emmar\\Pictures",
    r"C:\\Users\\emmar\\OneDrive\\Pictures",
]


def is_excluded(path: str) -> bool:
    if not path:
        return True
    normalized = os.path.abspath(path)
    for ex in EXCLUSION_ZONES:
        if normalized.startswith(os.path.abspath(ex)):
            return True
    return False


# -------------------------------------------------------------
# Permission API
# - request_permission(action, target, requester)
# - grant_permission(request_id, granter, duration_seconds)
# - revoke_permission(permission_id)
# - check_permission(action, target)
# -------------------------------------------------------------


def _make_id():
    return uuid.uuid4().hex


@eden_tool()
def request_permission(action: str, target: str, requester: str = "agent"):
    """
    Create a permission request. Returns a JSON object including
    `request_id` which a human should approve by calling `grant_permission(request_id)`.
    """
    if is_excluded(target):
        return [TextContent(type="text", text="Access denied: protected folder.")]

    data = _load_permissions()
    req_id = _make_id()
    data.setdefault("requests", {})[req_id] = {
        "action": action,
        "target": target,
        "requester": requester,
        "created_at": time.time(),
    }
    _save_permissions(data)

    _audit("request_created", {"request_id": req_id, "action": action, "target": target, "requester": requester})

    return [JsonContent(type="json", data={
        "status": "requested",
        "request_id": req_id,
        "instruction": f"Call grant_permission('{req_id}', granter='emma') to approve."
    })]


@eden_tool()
def grant_permission(request_id: str, granter: str = "emma", duration_seconds: int = None):
    """Approve a pending request and create a granted permission entry."""
    data = _load_permissions()
    req = data.get("requests", {}).get(request_id)
    if not req:
        return [TextContent(type="text", text="Request not found.")]

    perm_id = _make_id()
    expires_at = None
    if duration_seconds:
        expires_at = time.time() + int(duration_seconds)

    data.setdefault("permissions", {})[perm_id] = {
        "action": req["action"],
        "target": req["target"],
        "granted_by": granter,
        "granted_at": time.time(),
        "expires_at": expires_at,
        "allowed": True,
    }

    # remove request
    data.get("requests", {}).pop(request_id, None)
    _save_permissions(data)

    _audit("permission_granted", {"permission_id": perm_id, "granted_by": granter, "request_id": request_id})

    return [JsonContent(type="json", data={
        "status": "granted",
        "permission_id": perm_id,
        "action": data["permissions"][perm_id]["action"],
        "target": data["permissions"][perm_id]["target"],
    })]


@eden_tool()
def revoke_permission(permission_id: str):
    """Revoke a previously granted permission immediately."""
    data = _load_permissions()
    perm = data.get("permissions", {}).get(permission_id)
    if not perm:
        return [TextContent(type="text", text="Permission not found.")]
    perm["allowed"] = False
    perm["revoked_at"] = time.time()
    _save_permissions(data)
    _audit("permission_revoked", {"permission_id": permission_id})
    return [TextContent(type="text", text=f"Permission {permission_id} revoked.")]


def _check_permission_for(action: str, target: str, permission_id: str = None) -> (bool, str):
    """Return (allowed: bool, permission_id_or_message: str)"""
    data = _load_permissions()

    # allow explicit permission_id check if provided
    if permission_id:
        perm = data.get("permissions", {}).get(permission_id)
        if not perm:
            return False, "permission_not_found"
        if not perm.get("allowed", False):
            return False, "permission_not_allowed"
        if perm.get("expires_at") and time.time() > perm["expires_at"]:
            return False, "permission_expired"
        # match action and target by simple prefix matching for folders
        if perm["action"] != action:
            return False, "action_mismatch"
        if not (target == perm["target"] or target.startswith(perm["target"])):
            return False, "target_mismatch"
        return True, permission_id

    # without explicit permission_id, look up any matching allowed permission
    for pid, perm in data.get("permissions", {}).items():
        if not perm.get("allowed", False):
            continue
        if perm.get("expires_at") and time.time() > perm["expires_at"]:
            continue
        if perm["action"] != action:
            continue
        if target == perm["target"] or target.startswith(perm["target"]):
            return True, pid

    return False, "no_matching_permission"


# -------------------------------------------------------------
# File operations that use the permission model
# Each `*_secure` function creates a request; each `execute_*`
# function requires a `permission_id` returned from `grant_permission`.
# -------------------------------------------------------------


@eden_tool()
def read_file_secure(path: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Access denied: protected folder.")]
    # create a request
    return request_permission("read_file", path, requester="agent")


@eden_tool()
def execute_read(permission_id: str = None):
    allowed, info = _check_permission_for("read_file", "", permission_id)
    if not allowed:
        _audit("execute_read_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    # info is permission id
    data = _load_permissions()
    perm = data["permissions"][info]
    path = perm["target"]
    if is_excluded(path):
        return [TextContent(type="text", text="Access denied: protected folder.")]

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            _audit("execute_read_success", {"permission_id": info, "path": path, "bytes": len(content)})
            return [TextContent(type="text", text=content)]
    except Exception as e:
        _audit("execute_read_error", {"permission_id": info, "path": path, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]


@eden_tool()
def create_file(path: str, content: str = ""):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot create inside protected folder.")]
    return request_permission("create_file", path, requester="agent")


@eden_tool()
def execute_create(permission_id: str, content: str = ""):
    allowed, info = _check_permission_for("create_file", "", permission_id)
    if not allowed:
        _audit("execute_create_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    data = _load_permissions()
    perm = data["permissions"][info]
    path = perm["target"]
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot create inside protected folder.")]

    try:
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        _audit("execute_create_success", {"permission_id": info, "path": path, "bytes": len(content)})
        return [TextContent(type="text", text=f"File created: {path}")]
    except Exception as e:
        _audit("execute_create_error", {"permission_id": info, "path": path, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]


@eden_tool()
def move_file(source: str, destination: str):
    if is_excluded(source) or is_excluded(destination):
        return [TextContent(type="text", text="Cannot move files from/to protected folder.")]
    return request_permission("move_file", f"{source} -> {destination}", requester="agent")


@eden_tool()
def execute_move(permission_id: str):
    allowed, info = _check_permission_for("move_file", "", permission_id)
    if not allowed:
        _audit("execute_move_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    data = _load_permissions()
    perm = data["permissions"][info]
    source, dest = perm["target"].split(" -> ")
    if is_excluded(source) or is_excluded(dest):
        return [TextContent(type="text", text="Action blocked: protected folder.")]

    try:
        folder = os.path.dirname(dest)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        shutil.move(source, dest)
        _audit("execute_move_success", {"permission_id": info, "source": source, "dest": dest})
        return [TextContent(type="text", text=f"Moved {source} -> {dest}")]
    except Exception as e:
        _audit("execute_move_error", {"permission_id": info, "source": source, "dest": dest, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]


@eden_tool()
def rename_file(path: str, new_name: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot rename inside protected folder.")]

    folder = os.path.dirname(path)
    new_path = os.path.join(folder, new_name)
    return request_permission("rename_file", f"{path} -> {new_path}", requester="agent")


@eden_tool()
def execute_rename(permission_id: str):
    allowed, info = _check_permission_for("rename_file", "", permission_id)
    if not allowed:
        _audit("execute_rename_denied", {"permission_id": permission_id, "reason": info})
        return [TextContent(type="text", text=f"Permission denied: {info}")]

    data = _load_permissions()
    perm = data["permissions"][info]
    source, dest = perm["target"].split(" -> ")
    if is_excluded(source) or is_excluded(dest):
        return [TextContent(type="text", text="Cannot rename inside protected folder.")]

    try:
        os.rename(source, dest)
        _audit("execute_rename_success", {"permission_id": info, "source": source, "dest": dest})
        return [TextContent(type="text", text=f"Renamed {source} -> {dest}")]
    except Exception as e:
        _audit("execute_rename_error", {"permission_id": info, "source": source, "dest": dest, "error": str(e)})
        return [TextContent(type="text", text=f"Error: {e}")]


@eden_tool()
def map_directory(path: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot map protected folder.")]

    structure = {}

    for root, dirs, files in os.walk(path):
        if is_excluded(root):
            continue
        structure[root] = {
            "folders": [d for d in dirs if not is_excluded(os.path.join(root, d))],
            "files": files,
        }

    return [JsonContent(type="json", data=structure)]


@eden_tool()
def find_files(path: str, keyword: str):
    if is_excluded(path):
        return [TextContent(type="text", text="Cannot search inside protected folder.")]

    results = []

    for root, dirs, files in os.walk(path):
        if is_excluded(root):
            continue
        for f in files:
            if keyword.lower() in f.lower():
                results.append(os.path.join(root, f))

    return [JsonContent(type="json", data={"matches": results})]


@eden_tool()
def list_permissions():
    data = _load_permissions()
    return [JsonContent(type="json", data=data.get("permissions", {}))]


@eden_tool()
def list_requests():
    data = _load_permissions()
    return [JsonContent(type="json", data=data.get("requests", {}))]


@eden_tool()
def list_audit(limit: int = 100):
    data = _load_permissions()
    audit = data.get("audit", [])
    # return most recent entries first
    audit_sorted = sorted(audit, key=lambda e: e.get("ts", 0), reverse=True)
    return [JsonContent(type="json", data={"audit": audit_sorted[:limit]})]
