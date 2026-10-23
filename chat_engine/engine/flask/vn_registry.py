"""
Per-workspace Vanna instances.

The app used to keep one module-global ``vn`` shared by every request,
background job and channel. Whichever workspace was connected last won, for
everyone: a scheduled agent firing for workspace B silently switched every web
user of workspace A over to B's database.

``VannaRegistry`` caches one instance per workspace. ``VnRouter`` stands in
for the old global and forwards every attribute access to the instance that
belongs to the current caller, checked in this order:

1. a thread-local binding (``bind_instance`` / ``bound_to``). Background
   threads (scheduler, Teams bot workers) use this, as do requests that
   explicitly ensured a workspace;
2. the workspace in the caller's Flask session;
3. the last explicitly connected instance (the legacy "global" behavior);
4. a bare instance with no LLM/DB, for training-data-only operations.

Existing ``vn.<attr>`` call sites keep working unchanged through the proxy.
"""

import logging
import threading
from contextlib import contextmanager

from flask import has_request_context, session

logger = logging.getLogger(__name__)


class VannaRegistry:
    def __init__(self):
        self._instances = {}
        self._lock = threading.RLock()
        self._loader = None
        self._bare_factory = None
        self._bare = None

    def configure(self, loader=None, bare_factory=None):
        """loader(workspace_id) -> instance builds from the stored workspace
        config and raises ValueError with a user-facing reason on failure."""
        if loader is not None:
            self._loader = loader
        if bare_factory is not None:
            self._bare_factory = bare_factory

    def get(self, workspace_id):
        if not workspace_id:
            return None
        with self._lock:
            return self._instances.get(str(workspace_id))

    def put(self, workspace_id, instance):
        with self._lock:
            self._instances[str(workspace_id)] = instance

    def invalidate(self, workspace_id):
        """Drop the cached instance so the next use rebuilds it from the
        workspace's current saved config (call after any config save)."""
        with self._lock:
            removed = self._instances.pop(str(workspace_id), None)
        if removed is not None:
            logger.info(f"Vanna registry: invalidated instance for workspace {workspace_id}", extra={"admin": True})

    def get_or_build(self, workspace_id, refresh=False):
        """Returns (instance, error). Never raises."""
        if not workspace_id:
            return None, "No workspace id provided"
        wid = str(workspace_id)
        with self._lock:
            if not refresh and wid in self._instances:
                return self._instances[wid], None
            if self._loader is None:
                return None, "Vanna registry has no loader configured"
            try:
                instance = self._loader(wid)
            except ValueError as e:
                return None, str(e)
            except Exception as e:
                logger.error(f"Vanna registry: failed to build instance for workspace {wid}: {e}", exc_info=True, extra={"admin": True})
                return None, f"Failed to initialize Vanna: {e}"
            self._instances[wid] = instance
            logger.info(f"Vanna registry: built instance for workspace {wid}", extra={"admin": True})
            return instance, None

    def bare(self):
        with self._lock:
            if self._bare is None:
                if self._bare_factory is None:
                    raise RuntimeError("Vanna registry has no bare instance factory configured")
                self._bare = self._bare_factory()
            return self._bare


class VnRouter:
    def __init__(self, registry):
        object.__setattr__(self, "_registry", registry)
        object.__setattr__(self, "_local", threading.local())
        object.__setattr__(self, "_default", None)

    def bind_instance(self, instance):
        self._local.instance = instance

    def unbind_instance(self):
        self._local.instance = None

    @contextmanager
    def bound_to(self, instance):
        previous = getattr(self._local, "instance", None)
        self._local.instance = instance
        try:
            yield instance
        finally:
            self._local.instance = previous

    def set_default_instance(self, instance):
        object.__setattr__(self, "_default", instance)

    def resolve_instance(self):
        instance = getattr(self._local, "instance", None)
        if instance is not None:
            return instance

        if has_request_context():
            workspace_id = session.get("workspace_id")
            if workspace_id:
                instance, err = self._registry.get_or_build(workspace_id)
                if instance is not None:
                    return instance
                logger.warning(f"VnRouter: session workspace {workspace_id} unavailable: {err}")

        if self._default is not None:
            return self._default

        # Reaching here means nobody bound an instance and there's no session
        # workspace, so this caller gets an unconfigured instance. That used to
        # be masked by a process-global default set from /connect-vanna — i.e. by
        # silently borrowing whichever workspace connected last. Log it: a hit
        # here is a real missing bind, not something to paper over.
        logger.warning(
            "VnRouter: no bound instance and no session workspace — falling back to the "
            "bare instance. The caller should bind via ensure_vanna_initialized()."
        )
        return self._registry.bare()

    def __getattr__(self, name):
        return getattr(self.resolve_instance(), name)

    def __setattr__(self, name, value):
        setattr(self.resolve_instance(), name, value)

    def __repr__(self):
        return f"<VnRouter -> {self.resolve_instance()!r}>"
