"""
Phase 8 — automatic, workspace-isolated scheduling on the app's EXISTING
APScheduler instance.

create_warehouse_perf() is handed the BackgroundScheduler that
VannaFlaskApp.__init__ already runs for scheduled (slash-command) agents
(`scheduled_agents_scheduler`); no second scheduler is created. Onto it this
registers:

  wpa-reconcile              every RECONCILE_MINUTES: lists workspaces and makes
                             sure each one has exactly one analysis job, and
                             that deleted workspaces have none — so a NEW
                             workspace is picked up automatically, with no
                             admin action.
  wpa-analysis:<workspace>   every interval_minutes: run_analysis(<workspace>).
                             The workspace id is the job argument — the only
                             way a run learns which workspace it serves.

Same job options as the existing scheduled agents (max_instances=1,
coalesce=True, replace_existing=True, misfire grace). Each job body catches
everything, so a failing workspace never affects another workspace's job or
the scheduler thread. First runs are staggered to spread DB load.
"""
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

JOB_PREFIX = "wpa-analysis:"
RECONCILE_ID = "wpa-reconcile"
RECONCILE_MINUTES = 5
STAGGER_SECONDS = 45
FIRST_RUN_DELAY_SECONDS = 90


class WarehousePerfJobs:
    def __init__(self, scheduler, service, interval_minutes=60):
        self.scheduler = scheduler
        self.service = service
        self.interval_minutes = int(interval_minutes)
        self.active = False

    def start(self):
        if self.scheduler is None:
            logger.warning("warehouse_perf: no scheduler supplied — automatic analysis is disabled; "
                           "the dashboard can still run analyses on demand")
            return False
        # Aware instants (here and in queue_now below): APScheduler localises a
        # NAIVE datetime to the scheduler's own timezone, which isn't necessarily
        # this process's. Those matched only because both happen to be configured
        # the same today — change either and these jobs would fire hours out, with
        # nothing to show why.
        self.scheduler.add_job(func=self.reconcile, trigger="interval", minutes=RECONCILE_MINUTES,
                               id=RECONCILE_ID, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=20),
                               max_instances=1, coalesce=True, replace_existing=True, misfire_grace_time=120)
        self.active = True
        logger.info("warehouse_perf: registered on the existing scheduler (analysis every %d min per workspace)",
                    self.interval_minutes)
        return True

    def _job_ids(self):
        try:
            return {j.id for j in self.scheduler.get_jobs() if str(j.id).startswith(JOB_PREFIX)}
        except Exception:  # noqa: BLE001
            return set()

    def reconcile(self):
        """Adds a job for every workspace and removes jobs of deleted ones. Never raises."""
        try:
            workspaces = self.service.resolver.list_workspaces()
            if workspaces is None:   # read failure: change nothing
                return
            wanted = {JOB_PREFIX + w["workspace_id"]: w["workspace_id"] for w in workspaces}
            existing = self._job_ids()
            for i, (job_id, ws) in enumerate(sorted(wanted.items())):
                if job_id in existing:
                    continue
                self.scheduler.add_job(
                    func=self.run_workspace, args=[ws], trigger="interval", minutes=self.interval_minutes,
                    id=job_id, next_run_time=datetime.now(timezone.utc) + timedelta(
                        seconds=FIRST_RUN_DELAY_SECONDS + STAGGER_SECONDS * (i % 40)),
                    max_instances=1, coalesce=True, replace_existing=True, misfire_grace_time=300)
                logger.info("warehouse_perf: scheduled automatic analysis for workspace %s", ws)
            for job_id in existing - set(wanted):
                try:
                    self.scheduler.remove_job(job_id)
                    logger.info("warehouse_perf: removed analysis job for deleted workspace %s",
                                job_id[len(JOB_PREFIX):])
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            logger.exception("warehouse_perf: reconcile failed")

    def run_workspace(self, workspace_id):
        """Job body. Never raises."""
        try:
            self.service.run_analysis(workspace_id, trigger="scheduled")
        except Exception:  # noqa: BLE001
            logger.exception("warehouse_perf: scheduled analysis crashed for workspace %s", workspace_id)

    def queue_now(self, workspace_id, trigger="manual", actor=None):
        """Runs one analysis as soon as possible on the same scheduler (so the
        HTTP request returns immediately). Returns False if there's no scheduler."""
        if self.scheduler is None:
            return False
        self.scheduler.add_job(func=self._run_manual, args=[workspace_id, trigger, actor], trigger="date",
                               run_date=datetime.now(timezone.utc) + timedelta(seconds=1),
                               id=f"wpa-now:{workspace_id}", replace_existing=True, max_instances=1,
                               misfire_grace_time=300)
        return True

    def _run_manual(self, workspace_id, trigger, actor):
        try:
            self.service.run_analysis(workspace_id, trigger=trigger, actor=actor)
        except Exception:  # noqa: BLE001
            logger.exception("warehouse_perf: on-demand analysis crashed for workspace %s", workspace_id)

    def is_queued(self, workspace_id):
        try:
            return self.scheduler is not None and self.scheduler.get_job(f"wpa-now:{workspace_id}") is not None
        except Exception:  # noqa: BLE001
            return False

    def next_run(self, workspace_id):
        if self.scheduler is None:
            return None
        try:
            job = self.scheduler.get_job(JOB_PREFIX + str(workspace_id))
        except Exception:  # noqa: BLE001
            return None
        if job is None or job.next_run_time is None:
            return None
        return job.next_run_time.isoformat(timespec="seconds")

    def run_all_once(self):
        """Runs every workspace sequentially (used by tests and ops). Each run is
        isolated; returns {workspace_id: run_record_or_error}."""
        out = {}
        for w in self.service.resolver.list_workspaces() or []:
            try:
                out[w["workspace_id"]] = self.service.run_analysis(w["workspace_id"], trigger="scheduled")
            except Exception as exc:  # noqa: BLE001
                out[w["workspace_id"]] = {"status": "crashed", "failure_reason": type(exc).__name__}
        return out
