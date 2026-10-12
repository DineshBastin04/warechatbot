"""
Per-workspace result store — plain JSON files, no new database backend.

Layout (default root admin_store/warehouse_perf, next to the app's ChromaDB):
  <root>/<workspace_id>/catalog.json      discovered schema model (cache)
  <root>/<workspace_id>/latest.json       latest analysis summary pointer
  <root>/<workspace_id>/reports/<id>.json full report (structured result + text)
  <root>/<workspace_id>/runs.json         last RUN_HISTORY run records
  <root>/<workspace_id>/deliveries.json   email delivery audit + dedupe keys
  <root>/<workspace_id>/settings.json     Email settings (which saved recipients, when to send)
  <root>/<workspace_id>/run.lock          cross-process run lock

Each workspace has its own directory, so baselines, findings, reports and
delivery history can never be read across workspaces. The workspace id is
validated before it is used in a path. Writes are atomic (temp file +
os.replace) and serialised per workspace with a lock.
"""
import json
import os
import re
import shutil
import tempfile
import threading
import time
import uuid

_WS_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_REPORT_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
RUN_HISTORY = 200
REPORTS_KEPT = 90
DELIVERIES_KEPT = 1000
LOCK_STALE_SECONDS = 30 * 60


class StoreError(ValueError):
    pass


class WarehousePerfStore:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        os.makedirs(self.root, exist_ok=True)
        self._locks = {}
        self._locks_guard = threading.Lock()

    # ----------------------------------------------------------- plumbing
    def _dir(self, workspace_id):
        ws = str(workspace_id or "")
        if not _WS_RE.match(ws):
            raise StoreError("invalid workspace id")
        path = os.path.join(self.root, ws)
        os.makedirs(os.path.join(path, "reports"), exist_ok=True)
        return path

    def _lock(self, workspace_id):
        with self._locks_guard:
            return self._locks.setdefault(str(workspace_id), threading.RLock())

    def _read(self, workspace_id, name, default):
        path = os.path.join(self._dir(workspace_id), name)
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return default
        except (OSError, ValueError):
            return default

    def _write(self, workspace_id, name, obj):
        directory = self._dir(workspace_id)
        target = os.path.join(directory, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target), prefix=".tmp-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, default=str, ensure_ascii=False)
            os.replace(tmp, target)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------ catalog
    def get_catalog(self, workspace_id):
        return self._read(workspace_id, "catalog.json", None)

    def save_catalog(self, workspace_id, model):
        with self._lock(workspace_id):
            self._write(workspace_id, "catalog.json", model)

    def clear_catalog(self, workspace_id):
        with self._lock(workspace_id):
            try:
                os.unlink(os.path.join(self._dir(workspace_id), "catalog.json"))
            except FileNotFoundError:
                pass

    # ----------------------------------------------------------- settings
    def get_settings(self, workspace_id):
        return self._read(workspace_id, "settings.json", {}) or {}

    def save_settings(self, workspace_id, settings):
        with self._lock(workspace_id):
            self._write(workspace_id, "settings.json", settings)

    # ------------------------------------------------------------ reports
    def save_report(self, workspace_id, report):
        rid = report["report_id"]
        if not _REPORT_RE.match(rid):
            raise StoreError("invalid report id")
        with self._lock(workspace_id):
            self._write(workspace_id, os.path.join("reports", f"{rid}.json"), report)
            self._write(workspace_id, "latest.json", {"report_id": rid, "generated_at": report.get("generated_at")})
            self._prune_reports(workspace_id)

    def _prune_reports(self, workspace_id):
        rdir = os.path.join(self._dir(workspace_id), "reports")
        files = sorted((f for f in os.listdir(rdir) if f.endswith(".json")),
                       key=lambda f: os.path.getmtime(os.path.join(rdir, f)))
        for f in files[:-REPORTS_KEPT]:
            try:
                os.unlink(os.path.join(rdir, f))
            except OSError:
                pass

    def get_report(self, workspace_id, report_id):
        if not report_id or not _REPORT_RE.match(str(report_id)):
            return None
        return self._read(workspace_id, os.path.join("reports", f"{report_id}.json"), None)

    def latest_report(self, workspace_id):
        ptr = self._read(workspace_id, "latest.json", None)
        return self.get_report(workspace_id, ptr.get("report_id")) if ptr else None

    def list_reports(self, workspace_id, limit=30):
        rdir = os.path.join(self._dir(workspace_id), "reports")
        files = sorted((f for f in os.listdir(rdir) if f.endswith(".json")),
                       key=lambda f: os.path.getmtime(os.path.join(rdir, f)), reverse=True)[:limit]
        out = []
        for f in files:
            rep = self._read(workspace_id, os.path.join("reports", f), None)
            if rep:
                out.append({"report_id": rep["report_id"], "generated_at": rep.get("generated_at"),
                            "period": (rep.get("period") or {}).get("label"),
                            "classification": (rep.get("overall") or {}).get("classification"),
                            "alert_worthy": rep.get("alert_worthy")})
        return out

    # --------------------------------------------------------------- runs
    def append_run(self, workspace_id, record):
        with self._lock(workspace_id):
            runs = self._read(workspace_id, "runs.json", [])
            runs.append(record)
            self._write(workspace_id, "runs.json", runs[-RUN_HISTORY:])

    def list_runs(self, workspace_id, limit=20):
        return list(reversed(self._read(workspace_id, "runs.json", [])))[:limit]

    def last_run(self, workspace_id):
        runs = self._read(workspace_id, "runs.json", [])
        return runs[-1] if runs else None

    # --------------------------------------------------------- deliveries
    def begin_delivery(self, workspace_id, dedupe_key, label, address_masked, report_id, purpose):
        """Returns (delivery_id, already_sent). A key already recorded as sent is
        never sent again."""
        with self._lock(workspace_id):
            rows = self._read(workspace_id, "deliveries.json", [])
            for r in rows:
                if r.get("dedupe_key") == dedupe_key and r.get("status") in ("sent", "sending"):
                    return r["delivery_id"], True
            did = uuid.uuid4().hex[:12]
            rows.append({"delivery_id": did, "dedupe_key": dedupe_key, "report_id": report_id, "purpose": purpose,
                         "label": label, "address_masked": address_masked, "status": "sending", "attempts": 0,
                         "error": None, "created_at": time.time(), "updated_at": time.time()})
            self._write(workspace_id, "deliveries.json", rows[-DELIVERIES_KEPT:])
            return did, False

    def update_delivery(self, workspace_id, delivery_id, status, attempts, error=None):
        with self._lock(workspace_id):
            rows = self._read(workspace_id, "deliveries.json", [])
            for r in rows:
                if r.get("delivery_id") == delivery_id:
                    r.update({"status": status, "attempts": attempts, "error": error, "updated_at": time.time()})
            self._write(workspace_id, "deliveries.json", rows)

    def record_delivery(self, workspace_id, report_id, purpose, label, status, reason):
        with self._lock(workspace_id):
            rows = self._read(workspace_id, "deliveries.json", [])
            rows.append({"delivery_id": uuid.uuid4().hex[:12], "dedupe_key": None, "report_id": report_id,
                         "purpose": purpose, "label": label, "address_masked": None, "status": status,
                         "attempts": 0, "error": reason, "created_at": time.time(), "updated_at": time.time()})
            self._write(workspace_id, "deliveries.json", rows[-DELIVERIES_KEPT:])

    def list_deliveries(self, workspace_id, report_id=None, limit=100):
        rows = self._read(workspace_id, "deliveries.json", [])
        if report_id:
            rows = [r for r in rows if r.get("report_id") == report_id]
        return list(reversed(rows))[:limit]

    def auto_sends_on(self, workspace_id, day_iso):
        return len({r.get("report_id") for r in self._read(workspace_id, "deliveries.json", [])
                    if r.get("purpose") == "auto" and r.get("status") == "sent"
                    and str(r.get("dedupe_key") or "").startswith(f"auto:{day_iso}:")})

    # ---------------------------------------------------------- run lock
    def try_run_lock(self, workspace_id):
        """Cross-process, non-blocking. Returns a release() callable or None."""
        path = os.path.join(self._dir(workspace_id), "run.lock")
        for _ in range(2):
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as fh:
                    fh.write(f"{os.getpid()} {time.time()}")
                break
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(path) > LOCK_STALE_SECONDS:
                        os.unlink(path)
                        continue
                except OSError:
                    continue
                return None
        else:
            return None

        def release():
            try:
                os.unlink(path)
            except OSError:
                pass
        return release

    def delete_workspace(self, workspace_id):
        shutil.rmtree(self._dir(workspace_id), ignore_errors=True)
