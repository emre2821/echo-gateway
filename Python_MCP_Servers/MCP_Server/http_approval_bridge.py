"""Simple HTTP bridge to approve MCP-like file actions.

This bridge is intentionally minimal and for local development only.
It accepts POST /approve with JSON {action, target, requester} and
creates an immediate permission entry in `permissions.json`.

WARNING: This bridge will grant permissions immediately by default.
Run it only on localhost and understand the security implications.
"""
import json
import os
import uuid
import time
import logging
from flask import Flask, request, jsonify

ROOT = os.path.dirname(__file__)
PERMISSIONS_FILE = os.path.join(ROOT, 'permissions.json')

logger = logging.getLogger(__name__)

app = Flask('mcp-approval-bridge')


def _ensure_permissions_file():
    if os.path.exists(PERMISSIONS_FILE):
        return True

    try:
        os.makedirs(os.path.dirname(PERMISSIONS_FILE), exist_ok=True)
    except Exception as exc:
        logger.error('Could not ensure permissions directory exists at %s', os.path.dirname(PERMISSIONS_FILE), exc_info=exc)
        return False

    logger.warning('Permissions file not found at %s; a new file will be created on first write', PERMISSIONS_FILE)
    return True


if not _ensure_permissions_file():
    logger.error('Permissions file is not available at startup; approvals may fail until the path is fixed')


def _load():
    try:
        with open(PERMISSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'permissions': {}, 'requests': {}, 'audit': []}


def _save(data):
    try:
        with open(PERMISSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as exc:
        logger.error('Failed to write permissions file at %s', PERMISSIONS_FILE, exc_info=exc)
        return False


def _make_id():
    return uuid.uuid4().hex


@app.route('/approve', methods=['POST'])
def approve():
    body = request.get_json() or {}
    action = body.get('action')
    target = body.get('target')
    requester = body.get('requester')

    if not action or not target:
        return jsonify({'approved': False, 'reason': 'missing_fields'}), 400

    data = _load()
    perm_id = _make_id()
    data.setdefault('permissions', {})[perm_id] = {
        'action': action,
        'target': target,
        'granted_by': 'bridge',
        'granted_at': time.time(),
        'expires_at': None,
        'allowed': True,
    }
    data.setdefault('audit', []).append({
        'id': _make_id(),
        'event': 'bridge_grant',
        'details': {'action': action, 'target': target, 'requester': requester},
        'ts': time.time(),
    })
    if not _save(data):
        return jsonify({'approved': False, 'reason': 'persist_failed'}), 500

    return jsonify({'approved': True, 'permission_id': perm_id})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8765)
