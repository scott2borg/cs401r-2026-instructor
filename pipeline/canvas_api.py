"""
Idempotent Canvas REST API wrapper.
All write operations check for existing content before creating.
"""

import os
import requests
from urllib.parse import quote

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
        """Paginated GET. Defaults to per_page=100.

        Canvas defaults to **10 results per page**. This follows `next` links,
        so a missing per_page is not a correctness bug -- but every extra page
        is a round trip, and endpoints that omit the Link header return exactly
        10 items with no indication anything is missing. That is what made
        verify_course.py report 0 presentations and 0 pre-lab guides
        immediately after 26 successful uploads: it was seeing the first 10
        files in the course and nothing else.

        Callers that already specify per_page are left alone.
        """
        if "per_page=" not in path:
            path += ("&" if "?" in path else "?") + "per_page=100"
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
            gid = existing[name]
            # "Ensure" must mean ensure CORRECT, not merely ensure present.
            # This used to return early on a name match and never touch the
            # weight, so groups created under an older config kept their old
            # weights forever: after the weights moved to 49/30/10/11 on
            # 2026-08-05, Canvas was still holding Labs 60 and Final Project 25
            # and the run reported success.
            live = self._get(f"/assignment_groups/{gid}")
            current = live.json().get("group_weight") if live.ok else None
            if current is not None and float(current) != float(weight):
                self._put(f"/assignment_groups/{gid}",
                          {"group_weight": weight, "position": position})
                print(f"    ↩ Reweighted: {name} {current} -> {weight}")
            else:
                print(f"    ↩ Exists: {name} (weight {current})")
            return gid
        # FLAT parameters, not {"assignment_group": {...}}.
        #
        # Canvas's assignment-groups endpoint takes name / position /
        # group_weight at the top level, unlike assignments and modules which
        # DO use a nested wrapper. Sending the wrapper meant Canvas saw no name
        # and no weight, so every "created" group came back as an unnamed
        # "Assignments" at weight 0.0 -- and because the code only printed the
        # name it *intended*, the output said "Created: Labs" while Canvas held
        # something else. Seven duplicate groups accumulated this way before
        # anyone looked (2026-08-05).
        result = self._post("/assignment_groups",
                            {"name": name,
                             "group_weight": weight,
                             "position": position})
        if result:
            actual = result.get("name")
            if actual != name:
                print(f"    ✗ Canvas named it {actual!r}, expected {name!r} — not trusting this")
                return None
            print(f"    ✓ Created: {name} (weight {result.get('group_weight')})")
            return result["id"]
        return None

    def delete_assignment_group(self, group_id: int, move_to: int | None = None):
        """Delete an assignment group WITHOUT destroying its assignments.

        Canvas deletes every assignment inside a group unless the request says
        where to move them. This used to call plain DELETE, so removing the
        default "Assignments" group silently took any assignment filed there
        with it -- and assignments land there whenever a create omits
        assignment_group_id.

        Refuses to delete at all when there is nowhere to move them.
        """
        if move_to is None:
            print(f"    ! Skipping delete of group {group_id}: no destination "
                  f"for its assignments, and deleting would destroy them")
            return None
        return self._delete(f"/assignment_groups/{group_id}"
                            f"?move_assignments_to={move_to}")

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

    def get_module_items(self, module_id: int) -> list:
        return self._get_all(f"/modules/{module_id}/items?per_page=100")

    def add_module_item(self, module_id: int, item_type: str,
                        content_id: int, title: str):
        """Add a file, assignment, quiz, or page to a module -- ONCE.

        This used to be a bare POST with no existence check, so every run of
        build_course.py added another copy of every link. Four runs meant four
        identical entries per assignment in each module, which is what students
        would have seen. Canvas is perfectly happy to hold duplicates; nothing
        upstream complains.

        Match is on (type, content_id), not title: a renamed assignment is the
        same item and must not be added a second time.
        """
        for it in self.get_module_items(module_id):
            if it.get("type") == item_type and it.get("content_id") == content_id:
                return it["id"]
        r = self._post(f"/modules/{module_id}/items", {
            "module_item": {
                "title":      title,
                "type":       item_type,
                "content_id": content_id,
            }
        })
        return r["id"] if r else None

    def add_module_page(self, module_id: int, page_url: str, title: str):
        """Add a page to a module ONCE. Pages match on page_url, not content_id."""
        for it in self.get_module_items(module_id):
            if it.get("type") == "Page" and it.get("page_url") == page_url:
                return it["id"]
        r = self._post(f"/modules/{module_id}/items", {
            "module_item": {
                "title":    title,
                "type":     "Page",
                "page_url": page_url,
            }
        })
        return r["id"] if r else None

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
        """Return the id of a top-level course folder, creating it if needed.

        `/folders/by_path/<path>` returns the folder HIERARCHY as a LIST --
        root first, target last -- not a single folder object. Indexing it as
        a dict raises `TypeError: list indices must be integers`. That bug sat
        here unnoticed because every caller of this function (stages 1, 2 and
        3) failed on it, so no stage that uploads a file had ever completed.
        """
        r = self._get(f"/folders/by_path/{quote(name)}")
        if r.ok:
            data = r.json()
            if isinstance(data, list):
                return data[-1]["id"] if data else None
            if isinstance(data, dict) and "id" in data:
                return data["id"]

        # parent_folder_path "/" does not name anything Canvas recognises: a
        # course's root folder is called "course files". Creation therefore
        # failed for every folder that did not already exist, and stage 2
        # aborted with "Cannot create Readings folder". Lab Guides and
        # Pre-Lab Guides only worked because a file upload had implicitly
        # created them earlier. Resolve the real root and parent by id.
        root = self._get("/folders/root")
        payload = {"name": name}
        if root.ok and isinstance(root.json(), dict) and root.json().get("id"):
            payload["parent_folder_id"] = root.json()["id"]
        else:
            payload["parent_folder_path"] = "course files"
        result = requests.post(f"{self.root}/folders",
                               headers=self.headers, json=payload)
        if result.ok:
            body = result.json()
            if isinstance(body, dict) and "id" in body:
                return body["id"]
            print(f"    ✗ Folder create returned no id for '{name}': {str(body)[:120]}")
            return None

        # A folder that already exists comes back 409; re-read rather than fail.
        if result.status_code == 409:
            r2 = self._get(f"/folders/by_path/{quote(name)}")
            if r2.ok:
                d2 = r2.json()
                return (d2[-1]["id"] if isinstance(d2, list) and d2
                        else d2.get("id") if isinstance(d2, dict) else None)

        print(f"    ✗ Could not get or create folder '{name}': "
              f"{result.status_code} {result.text[:120]}")
        return None

    def upload_file(self, local_path: str, canvas_name: str,
                    folder_id: int, content_type: str = "application/octet-stream") -> int | None:
        size = os.path.getsize(local_path)
        # Step 1: request upload slot
        r = requests.post(
            f"{self.base_url}/api/v1/courses/{self.course_id}/files",
            headers=self.headers,
            # parent_folder_id, NOT folder_id. Canvas's file-upload endpoint
            # does not recognise `folder_id`; it ignored the parameter silently
            # and filed all 55 uploads under "unfiled" while every folder the
            # pipeline had just created sat empty. The upload returned a real
            # file id each time, so nothing anywhere reported a problem.
            json={"name": canvas_name, "size": size,
                  "content_type": content_type,
                  "parent_folder_id": folder_id, "on_duplicate": "overwrite"})
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
