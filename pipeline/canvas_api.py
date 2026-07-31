"""
Idempotent Canvas REST API wrapper.
All write operations check for existing content before creating.
"""

import os
import requests

class CanvasAPI:
    def __init__(self, base_url: str, course_id: str, token: str):
        self.base_url  = base_url.rstrip("/")
        self.course_id = course_id
        self.root      = f"{self.base_url}/api/v1/courses/{course_id}"
        self.headers   = {"Authorization": f"Bearer {token}",
                          "Content-Type": "application/json"}

    # ── Core request helpers ─────────────────────────────────────────────────

    def _get(self, path: str) -> requests.Response:
        return requests.get(f"{self.root}{path}", headers=self.headers)

    def _post(self, path: str, data: dict) -> dict | None:
        r = requests.post(f"{self.root}{path}", headers=self.headers, json=data)
        if not r.ok:
            print(f"    ✗ {r.status_code} POST {path}: {r.text[:200]}")
            return None
        return r.json()

    def _put(self, path: str, data: dict) -> dict | None:
        r = requests.put(f"{self.root}{path}", headers=self.headers, json=data)
        if not r.ok:
            print(f"    ✗ {r.status_code} PUT {path}: {r.text[:200]}")
            return None
        return r.json()

    def _delete(self, path: str) -> bool:
        r = requests.delete(f"{self.root}{path}", headers=self.headers)
        return r.ok

    def _get_all(self, path: str) -> list:
        results, url = [], f"{self.root}{path}"
        while url:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            results.extend(r.json())
            url = r.links.get("next", {}).get("url")
        return results

    # ── Course settings ──────────────────────────────────────────────────────

    def set_course_dates(self, start_iso: str, end_iso: str):
        return self._put("", {"course": {
            "start_at": start_iso,
            "end_at":   end_iso,
            "restrict_enrollments_to_course_dates": True,
        }})

    def set_weighted_grading(self, enabled: bool = True):
        return self._put("", {"course": {"apply_assignment_group_weights": enabled}})

    def set_syllabus(self, html: str):
        return self._put("", {"course": {"syllabus_body": html}})

    # ── Assignment groups ────────────────────────────────────────────────────

    def get_assignment_groups(self) -> dict:
        groups = self._get_all("/assignment_groups")
        return {g["name"]: g["id"] for g in groups}

    def ensure_assignment_group(self, name: str, weight: int, position: int,
                                existing: dict) -> int:
        if name in existing:
            print(f"    ↩ Exists: {name}")
            return existing[name]
        result = self._post("/assignment_groups",
                            {"assignment_group": {"name": name,
                                                  "group_weight": weight,
                                                  "position": position}})
        if result:
            print(f"    ✓ Created: {name}")
            return result["id"]
        return None

    def delete_assignment_group(self, group_id: int):
        self._delete(f"/assignment_groups/{group_id}")

    # ── Modules ──────────────────────────────────────────────────────────────

    def get_modules(self) -> dict:
        modules = self._get_all("/modules?per_page=50")
        return {m["name"]: m["id"] for m in modules}

    def ensure_module(self, name: str, position: int, existing: dict) -> int:
        if name in existing:
            return existing[name]
        result = self._post("/modules",
                            {"module": {"name": name, "position": position}})
        if result:
            print(f"    ✓ Module: {name}")
            return result["id"]
        return None

    def add_module_item(self, module_id: int, item_type: str,
                        content_id: int, title: str):
        """Add a file, assignment, quiz, or page to a module."""
        self._post(f"/modules/{module_id}/items", {
            "module_item": {
                "title":      title,
                "type":       item_type,
                "content_id": content_id,
            }
        })

    def add_module_page(self, module_id: int, page_url: str, title: str):
        self._post(f"/modules/{module_id}/items", {
            "module_item": {
                "title":    title,
                "type":     "Page",
                "page_url": page_url,
            }
        })

    # ── Assignments ──────────────────────────────────────────────────────────

    def get_assignments(self) -> dict:
        items = self._get_all("/assignments?per_page=100")
        return {a["name"]: a["id"] for a in items}

    def ensure_assignment(self, payload: dict, existing: dict) -> int:
        name = payload["assignment"]["name"]
        if name in existing:
            aid = existing[name]
            self._put(f"/assignments/{aid}", payload)
            print(f"    ↩ Updated: {name}")
            return aid
        result = self._post("/assignments", payload)
        if result:
            print(f"    ✓ Created: {name}")
            return result["id"]
        return None

    # ── Quizzes ──────────────────────────────────────────────────────────────

    def get_quizzes(self) -> dict:
        items = self._get_all("/quizzes?per_page=100")
        return {q["title"]: q["id"] for q in items}

    def ensure_quiz(self, payload: dict, existing: dict) -> int:
        title = payload["quiz"]["title"]
        if title in existing:
            qid = existing[title]
            self._put(f"/quizzes/{qid}", payload)
            print(f"    ↩ Updated: {title}")
            return qid
        result = self._post("/quizzes", payload)
        if result:
            print(f"    ✓ Created: {title}")
            return result["id"]
        return None

    def get_quiz_questions(self, quiz_id: int) -> list:
        return self._get_all(f"/quizzes/{quiz_id}/questions")

    def delete_quiz_question(self, quiz_id: int, question_id: int):
        self._delete(f"/quizzes/{quiz_id}/questions/{question_id}")

    def add_quiz_question(self, quiz_id: int, payload: dict) -> bool:
        result = self._post(f"/quizzes/{quiz_id}/questions", payload)
        return result is not None

    # ── Pages ────────────────────────────────────────────────────────────────

    def get_pages(self) -> dict:
        items = self._get_all("/pages?per_page=100")
        return {p["title"]: p["url"] for p in items}

    def ensure_page(self, title: str, body: str, existing: dict,
                    published: bool = False) -> str:
        if title in existing:
            page_url = existing[title]
            self._put(f"/pages/{page_url}",
                      {"wiki_page": {"title": title, "body": body,
                                     "published": published}})
            print(f"    ↩ Updated: {title}")
            return page_url
        result = self._post("/pages",
                             {"wiki_page": {"title": title, "body": body,
                                            "published": published}})
        if result:
            print(f"    ✓ Created: {title}")
            return result.get("url", "")
        return ""

    def set_front_page(self, page_url: str):
        self._put(f"/pages/{page_url}",
                  {"wiki_page": {"front_page": True, "published": True}})

    # ── Files ────────────────────────────────────────────────────────────────

    def get_or_create_folder(self, name: str) -> int | None:
        r = self._get(f"/folders/by_path/{name}")
        if r.ok:
            return r.json()["id"]
        result = requests.post(f"{self.root}/folders",
                               headers=self.headers,
                               json={"name": name,
                                     "parent_folder_path": "/"})
        return result.json()["id"] if result.ok else None

    def upload_file(self, local_path: str, canvas_name: str,
                    folder_id: int, content_type: str = "application/octet-stream") -> int | None:
        size = os.path.getsize(local_path)
        # Step 1: request upload slot
        r = requests.post(
            f"{self.base_url}/api/v1/courses/{self.course_id}/files",
            headers=self.headers,
            json={"name": canvas_name, "size": size,
                  "content_type": content_type,
                  "folder_id": folder_id, "on_duplicate": "overwrite"})
        if not r.ok:
            print(f"    ✗ Upload slot failed: {r.text[:150]}")
            return None
        info = r.json()
        # Step 2: upload to pre-signed URL
        with open(local_path, "rb") as f:
            r2 = requests.post(info["upload_url"], data=info["upload_params"],
                               files=[("file", (canvas_name, f, content_type))],
                               allow_redirects=False)
        # Step 3: follow confirmation redirect
        if r2.status_code in (301, 302, 303):
            r2 = requests.get(r2.headers["Location"], headers=self.headers)
        return r2.json().get("id") if r2.ok else None
