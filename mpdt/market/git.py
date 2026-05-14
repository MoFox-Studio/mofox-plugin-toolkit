"""Local git helpers for market publishing."""

from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import quote


class GitError(RuntimeError):
    """Raised when a git command fails."""


def run_git(args: list[str], cwd: Path, *, check: bool = True) -> str:
    """Run a git command and return stdout."""

    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if check and result.returncode != 0:
        message = (result.stderr or result.stdout or "git command failed").strip()
        raise GitError(message)
    return result.stdout.strip()


def ensure_git_repo(plugin_dir: Path) -> None:
    """Initialize a git repository when the plugin directory is not one yet."""

    if (plugin_dir / ".git").exists():
        return
    run_git(["init"], plugin_dir)


def has_remote(plugin_dir: Path, name: str = "origin") -> bool:
    """Return whether a git remote exists."""

    try:
        run_git(["remote", "get-url", name], plugin_dir)
        return True
    except GitError:
        return False


def set_remote(plugin_dir: Path, url: str, name: str = "origin") -> None:
    """Add or update the git remote URL."""

    if has_remote(plugin_dir, name):
        run_git(["remote", "set-url", name, url], plugin_dir)
    else:
        run_git(["remote", "add", name, url], plugin_dir)


def has_commits(plugin_dir: Path) -> bool:
    """Return whether the repository has at least one commit."""

    try:
        run_git(["rev-parse", "--verify", "HEAD"], plugin_dir)
        return True
    except GitError:
        return False


def ensure_commit(plugin_dir: Path, message: str) -> None:
    """Commit current changes when there is anything staged or unstaged."""

    run_git(["add", "."], plugin_dir)
    status = run_git(["status", "--porcelain"], plugin_dir)
    if not status and has_commits(plugin_dir):
        return
    run_git(["commit", "-m", message], plugin_dir)


def current_branch(plugin_dir: Path) -> str:
    """Return the current branch name, defaulting to main for unborn repos."""

    branch = run_git(["branch", "--show-current"], plugin_dir, check=False)
    return branch or "main"


def tag_exists(plugin_dir: Path, tag: str) -> bool:
    """Return whether a local tag exists."""

    return bool(run_git(["tag", "--list", tag], plugin_dir, check=False))


def ensure_tag(plugin_dir: Path, tag: str) -> None:
    """Create a local tag if it does not exist."""

    if not tag_exists(plugin_dir, tag):
        run_git(["tag", tag], plugin_dir)


def github_push_url(owner: str, repo: str, token: str) -> str:
    """Return a temporary authenticated GitHub push URL."""

    return f"https://x-access-token:{quote(token, safe='')}@github.com/{owner}/{repo}.git"


def push_branch_and_tag(plugin_dir: Path, branch: str, tag: str, remote: str = "origin") -> None:
    """Push the branch and tag to origin."""

    run_git(["push", remote, f"HEAD:{branch}"], plugin_dir)
    run_git(["push", remote, tag], plugin_dir)
