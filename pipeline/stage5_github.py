"""
Stage 5 — GitHub Classroom Integration

For each lab:
  1. Creates a private template repository in your GitHub org
     (or gets the existing one)
  2. Pushes starter kit files to the template repo
  3. Creates a GitHub Classroom assignment linked to the template repo
  4. Returns {lab_number: invite_link} for linking into Canvas

Environment variables (all required):
    GITHUB_TOKEN         Personal access token with scopes:
                           repo, read:org, manage_billing:github (for Classroom API)
    GITHUB_ORG           GitHub org or user owning the template repos
                           (e.g. "byu-cs401r")
    GITHUB_CLASSROOM_ID  Numeric ID of your GitHub Classroom
                           (find it at: https://classroom.github.com/classrooms)

Finding your Classroom ID:
    curl -H "Authorization: Bearer $GITHUB_TOKEN" \
         https://api.github.com/classrooms

Usage:
    export GITHUB_TOKEN="ghp_..."
    export GITHUB_ORG="byu-cs401r"
    export GITHUB_CLASSROOM_ID="12345"
    python build_course.py --stage 5
"""

import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone

import requests

GITHUB_API  = "https://api.github.com"
MDT         = timezone(timedelta(hours=-6))

# script_dir = CS_401R_2026/ folder (one level above pipeline/)
_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ─────────────────────────────────────────────────────────────────────────────
# GitHub REST API wrapper
# ─────────────────────────────────────────────────────────────────────────────

class _GitHub:
    def __init__(self, token: str, org: str):
        self.org     = org
        self.headers = {
            "Authorization":        f"Bearer {token}",
            "Accept":               "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._token = token

    def _get(self, path: str) -> requests.Response:
        return requests.get(f"{GITHUB_API}{path}", headers=self.headers)

    def _post(self, path: str, data: dict) -> requests.Response:
        return requests.post(f"{GITHUB_API}{path}", headers=self.headers, json=data)

    # ── Repos ────────────────────────────────────────────────────────────────

    def get_repo(self, name: str) -> dict | None:
        r = self._get(f"/repos/{self.org}/{name}")
        return r.json() if r.ok else None

    def create_repo(self, name: str, description: str = "") -> dict | None:
        """Create a private template repo in the org (or user account)."""
        # Try org endpoint first; fall back to user endpoint
        for endpoint in [f"/orgs/{self.org}/repos", "/user/repos"]:
            r = self._post(endpoint, {
                "name":        name,
                "description": description,
                "private":     True,
                "is_template": True,
                "auto_init":   True,    # creates main branch with README
            })
            if r.ok:
                return r.json()
        print(f"    ✗ Could not create repo {name}: {r.status_code} {r.text[:200]}")
        return None

    def get_or_create_repo(self, name: str, description: str = "") -> dict | None:
        repo = self.get_repo(name)
        if repo:
            print(f"    ↩ Repo exists: {self.org}/{name}")
            return repo
        repo = self.create_repo(name, description)
        if repo:
            print(f"    ✓ Repo created: {self.org}/{name}")
        return repo

    # ── Starter kit push ─────────────────────────────────────────────────────

    def push_starter_kit(self, repo_name: str, source_dir: str) -> bool:
        """
        Clone the template repo, copy starter kit files, commit and push.
        Uses a token-authenticated HTTPS URL — no SSH key needed.
        """
        if not os.path.isdir(source_dir):
            print(f"    ✗ Source dir not found: {source_dir}")
            return False

        clone_url = f"https://{self._token}@github.com/{self.org}/{repo_name}.git"
        tmp = tempfile.mkdtemp(prefix="gh_kit_")
        try:
            # Clone
            r = subprocess.run(
                ["git", "clone", "--depth=1", clone_url, tmp],
                capture_output=True, text=True)
            if r.returncode != 0:
                print(f"    ✗ git clone failed: {r.stderr[:200]}")
                return False

            # Copy starter kit content into the clone
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(tmp, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)

            # Ensure a .gitignore is present (never commit credentials)
            gitignore = os.path.join(tmp, ".gitignore")
            if not os.path.exists(gitignore):
                with open(gitignore, "w") as f:
                    f.write(
                        "*.tfvars\n.env\n*.tfstate\n*.tfstate.backup\n"
                        ".terraform/\n__pycache__/\n*.pyc\n.DS_Store\n"
                        "*.zip\n.aws/\n"
                    )

            # Git identity (required for commit)
            subprocess.run(["git", "config", "user.email", "pipeline@byu.edu"],
                           cwd=tmp, capture_output=True)
            subprocess.run(["git", "config", "user.name", "CS401R Pipeline"],
                           cwd=tmp, capture_output=True)

            # Stage, commit, push
            subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True)
            r = subprocess.run(
                ["git", "commit", "-m", "Add starter kit files\n\nPushed by CS401R course pipeline.",
                 "--allow-empty"],
                cwd=tmp, capture_output=True, text=True)
            r = subprocess.run(["git", "push"], cwd=tmp, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"    ✗ git push failed: {r.stderr[:200]}")
                return False

            print(f"    ✓ Starter kit pushed to {self.org}/{repo_name}")
            return True

        except Exception as e:
            print(f"    ✗ Unexpected error: {e}")
            return False
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Classroom API wrapper
# ─────────────────────────────────────────────────────────────────────────────

class _Classroom:
    def __init__(self, token: str, classroom_id: int):
        self.id      = classroom_id
        self.headers = {
            "Authorization":        f"Bearer {token}",
            "Accept":               "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_assignments(self) -> dict[str, dict]:
        """Return {title: assignment_dict} for all existing assignments."""
        r = requests.get(f"{GITHUB_API}/classrooms/{self.id}/assignments",
                         headers=self.headers)
        if not r.ok:
            print(f"    ✗ Could not fetch assignments: {r.status_code} {r.text[:200]}")
            return {}
        return {a["title"]: a for a in r.json()}

    def create_assignment(self, title: str, repo_id: int,
                          deadline_iso: str | None = None) -> dict | None:
        payload = {
            "title":                       title,
            "type":                        "individual",
            "starter_code_repository_id":  repo_id,
            "public_repo":                 False,
        }
        if deadline_iso:
            payload["deadline"] = deadline_iso

        r = requests.post(
            f"{GITHUB_API}/classrooms/{self.id}/assignments",
            headers=self.headers, json=payload)
        if not r.ok:
            print(f"    ✗ Assignment creation failed: {r.status_code} {r.text[:250]}")
            return None
        return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# Main stage function
# ─────────────────────────────────────────────────────────────────────────────

def run(cfg: dict) -> dict[int, str]:
    """
    Create GitHub template repos and GitHub Classroom assignments for each lab.

    Returns:
        {lab_number: invite_link}  — empty string if assignment creation failed.
    """
    print("\n[Stage 5] GitHub Classroom Integration")

    token       = os.environ.get("GITHUB_TOKEN", "").strip()
    org         = os.environ.get("GITHUB_ORG", "").strip()
    cls_id_str  = os.environ.get("GITHUB_CLASSROOM_ID", "").strip()

    missing = [k for k, v in {"GITHUB_TOKEN": token,
                               "GITHUB_ORG":   org,
                               "GITHUB_CLASSROOM_ID": cls_id_str}.items() if not v]
    if missing:
        print(f"  ✗ Missing environment variables: {', '.join(missing)}")
        print()
        print("  How to find your Classroom ID:")
        print("    curl -H 'Authorization: Bearer $GITHUB_TOKEN' \\")
        print("         https://api.github.com/classrooms")
        return {}

    classroom_id = int(cls_id_str)
    gh           = _GitHub(token, org)
    classroom    = _Classroom(token, classroom_id)

    print(f"  Org: {org}")
    print(f"  Classroom ID: {classroom_id}")

    existing = classroom.get_assignments()
    invite_links: dict[int, str] = {}

    for lab in cfg["labs"]:
        n       = lab["number"]
        title   = lab["title"]
        due     = lab["due"]
        kit_rel = lab.get("starter_kit")

        assignment_title = f"Lab {n} — {title}"
        repo_name        = f"cs401r-lab{n}-template"
        source_dir       = os.path.join(_SCRIPT_DIR, kit_rel) if kit_rel else None

        print(f"\n  Lab {n} — {title}")

        # 1. Create / get template repo
        repo = gh.get_or_create_repo(
            repo_name,
            f"CS 401R Lab {n}: {title} — starter template (do not fork directly)")
        if not repo:
            continue
        repo_id = repo["id"]

        # 2. Push starter kit content (if available)
        if source_dir and os.path.isdir(source_dir):
            gh.push_starter_kit(repo_name, source_dir)
        else:
            print(f"    ↩ No starter kit configured for Lab {n} — template repo is empty shell")

        # 3. Create / get Classroom assignment
        if assignment_title in existing:
            a = existing[assignment_title]
            invite = a.get("invite_link", "")
            print(f"    ↩ Assignment exists (id={a['id']})")
        else:
            deadline_dt  = datetime.strptime(due, "%Y-%m-%d").replace(
                hour=23, minute=59, second=0, tzinfo=MDT)
            deadline_iso = deadline_dt.isoformat()

            a = classroom.create_assignment(assignment_title, repo_id, deadline_iso)
            invite = a.get("invite_link", "") if a else ""
            if invite:
                print(f"    ✓ Assignment created (id={a['id']})")
            else:
                print(f"    ✗ Assignment creation failed — see error above")

        invite_links[n] = invite
        if invite:
            print(f"    → Invite link: {invite}")

    # Summary
    ok = sum(1 for v in invite_links.values() if v)
    print(f"\n  {ok}/{len(cfg['labs'])} assignments ready with invite links")
    if ok < len(cfg["labs"]):
        print("\n  For labs without invite links, create the assignment manually")
        print("  at https://classroom.github.com and paste the link here:")
        print("  course_config.yaml → labs[N].github_invite_link")

    if invite_links:
        print("\n  Invite links (share these on Canvas or by email):")
        for lab in cfg["labs"]:
            n = lab["number"]
            link = invite_links.get(n, "")
            status = link if link else "(not available)"
            print(f"    Lab {n}: {status}")

    print("\n  ✓ Stage 5 complete")
    return invite_links
