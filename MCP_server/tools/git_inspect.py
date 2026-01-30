"""
tools/git_inspect.py

Read-only Git inspection tool for MCP Server.

Single-file, stdlib-only, auto-discoverable via @eden_tool(). It runs a
small set of read-only git commands with timeouts and returns a JSON-able
report. Respects organizer exclusions and fails gracefully when not a
git repo.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from . import JsonContent, eden_tool

try:
    from .organizer_tools import is_excluded
except Exception:
    def is_excluded(path: str) -> bool:  # type: ignore
        return False


DEFAULT_TIMEOUT = 5.0


def _run_git(args: List[str], cwd: Path,
             timeout: float = DEFAULT_TIMEOUT) -> Dict[str, object]:
    cmd = ["git"] + args
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "rc": p.returncode,
            "out": p.stdout.strip(),
            "err": p.stderr.strip(),
            "timeout": False,
        }
    except subprocess.TimeoutExpired as e:
        return {"rc": -1, "out": "", "err": str(e), "timeout": True}


def _parse_head(raw: str) -> Optional[Dict[str, str]]:
    if not raw:
        return None
    # Expecting lines: hash\nauthor\ndate\nsubject
    parts = raw.splitlines()
    if len(parts) < 4:
        # try a one-line format
        one = parts[0].strip()
        return {"hash": one, "author": "", "date": "", "subject": ""}
    return {
        "hash": parts[0].strip(),
        "author": parts[1].strip(),
        "date": parts[2].strip(),
        "subject": parts[3].strip(),
    }


@eden_tool()
def git_inspect(repo_path: str) -> List[object]:
    """Inspect a git repository at `repo_path` and return metadata.

    Returns a single JsonContent item with keys:
      is_git_repo, repo_root, current_branch, head_commit,
      status_summary, remotes, error
    """
    report: Dict[str, object] = {
        "is_git_repo": False,
        "repo_root": None,
        "current_branch": None,
        "head_commit": None,
        "status_summary": None,
        "remotes": [],
        "error": None,
    }

    try:
        p = Path(repo_path)
        if not p.exists() or not p.is_dir():
            raise FileNotFoundError("Path not found or not a directory")

        if is_excluded(str(p)):
            raise PermissionError("Access denied: protected path")

        # is it a git repo?
        res = _run_git(["rev-parse", "--show-toplevel"], p)
        if res.get("rc") != 0 or res.get("timeout"):
            report["is_git_repo"] = False
            report["error"] = res.get("err") or "not a git repo"
            return [JsonContent(type="json", data=report)]

        report["is_git_repo"] = True
        repo_root = res.get("out")
        report["repo_root"] = repo_root

        # current branch
        res = _run_git(["branch", "--show-current"], p)
        if res.get("rc") == 0:
            report["current_branch"] = res.get("out") or None

        # head commit
        fmt = "%H%n%an%n%ai%n%s"
        res = _run_git(["log", "-1", "--pretty=format:" + fmt], p)
        if res.get("rc") == 0:
            report["head_commit"] = _parse_head(res.get("out"))

        # status
        res = _run_git(["status", "--porcelain"], p)
        status = {"clean": True, "counts": {}, "porcelain": []}
        if res.get("rc") == 0:
            lines = [ln for ln in res.get("out", "").splitlines() if ln]
            status["porcelain"] = lines
            if lines:
                status["clean"] = False
            # simple counts
            added = modified = deleted = untracked = 0
            others = 0
            for ln in lines:
                if ln.startswith("??"):
                    untracked += 1
                    continue
                code = ln[:2]
                if "A" in code:
                    added += 1
                elif "M" in code:
                    modified += 1
                elif "D" in code:
                    deleted += 1
                else:
                    others += 1
            status["counts"] = {
                "added": added,
                "modified": modified,
                "deleted": deleted,
                "untracked": untracked,
                "others": others,
            }
        report["status_summary"] = status

        # remotes
        res = _run_git(["remote", "-v"], p)
        rems: Dict[str, set] = {}
        if res.get("rc") == 0:
            for ln in res.get("out", "").splitlines():
                parts = ln.split()
                if len(parts) < 2:
                    continue
                name = parts[0].strip()
                url = parts[1].strip()
                rems.setdefault(name, set()).add(url)
        report["remotes"] = [
            {"name": n, "urls": sorted(list(urls))} for n, urls in rems.items()
        ]

    except Exception as e:
        report["error"] = str(e)

    return [JsonContent(type="json", data=report)]
