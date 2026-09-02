#!/usr/bin/env python3
"""Lane-orchestration state: an append-only ledger, reducer, locks and receipts.

The ledger deliberately copies the design of
``skills/clodex/state/clodex_state.py`` and ``state/reducer.py``:

    events.ndjson   append-only, fsync'd authority
    run.json        atomically written, derived convenience snapshot
    lock.json       session ownership and liveness
    write.lock      advisory flock for short writes

The log is reduced before a candidate event is written.  A torn final line is
repaired using the same rule used by the reader, and a refused event leaves
the existing log untouched.  Receipts use the same pending/external-action/
reconcile discipline as clodex ship operations, with an operation-specific
oracle so an old attempt cannot satisfy a new one.

This is a deliberate copy, not an import, because the two engines diverge in
two structural ways.  This engine has its own frozen orchestrator vocabulary
and reducer rather than clodex's event schema, and its identity is a
run-plan path plus full SHA in an external ``~/.lane-orchestrator`` ledger
rather than a repo ``.clodex/<run-id>`` directory.  It therefore does not
import or modify the clodex state files.  It also never spawns a process:
recovery scans ``/proc`` directly for the wrapper's operation id; dispatch is
owned by ``dispatch_wrapper.py``.  Finally, unlock has no force escape hatch:
live and unidentifiable holders are refused, period.

CLI payloads arrive on stdin, and exit codes retain clodex's meanings:

    0  success
    1  refused, nothing written (except a reconcile that has already recorded
       an outcome and then reports its result)
    2  usage error
    3  append is durably in the log but the derived snapshot was not refreshed

Stdlib only, Python 3.9+.  POSIX (uses ``fcntl`` for the write lock).
"""

import argparse
import datetime as _datetime
import errno
import fcntl
import hashlib
import json
import logging
import math
import os
import secrets
import sys
import tempfile
import time
from contextlib import contextmanager


SCHEMA_VERSION = 1
EVENTS_FILE = "events.ndjson"
SNAPSHOT_FILE = "run.json"
LOCK_FILE = "lock.json"
WRITE_LOCK_FILE = "write.lock"
LOCK_TOKEN_ENV = "LANE_ORCHESTRATOR_LOCK_TOKEN"
WRITE_LOCK_TIMEOUT = 30.0

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_PARTIAL = 3

EVENT_TYPES = (
    "orch:run:opened",
    "lane:dispatched",
    "lane:spawning",
    "lane:launched",
    "lane:settled",
    "claude:leg",
    "lane:parked",
    "lane:unparked",
    "lane:completed",
    "gate:evaluated",
    "budget:sampled",
    "orch:run:closed",
)

__all__ = [
    "SCHEMA_VERSION", "EVENT_TYPES", "OrchestratorStateError", "ClodexStateError",
    "ReducerInvariantError", "RunLocked", "append_event", "rebuild", "load_snapshot",
    "atomic_write_snapshot", "acquire_lock", "break_lock", "Lock", "events_path",
    "snapshot_path", "lock_path", "write_lock_path", "load_schema", "validate",
    "validate_run_plan", "run_plan_sha", "compute_run_plan_sha", "ledger_dir_for",
    "open_run", "unpark", "mint_op_id", "oracle_for", "marker_for", "create_receipt",
    "dispatch_receipt", "mark_spawning", "mark_launched", "settle", "reconcile",
    "check_ledger_identity",
]

_WOULD_BLOCK = (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK)
_WRITE_LOCKS = {}
_LOG = logging.getLogger("lane.orchestrator.state")


class OrchestratorStateError(Exception):
    """Any refusal to read or write the orchestrator ledger."""


class ReducerInvariantError(OrchestratorStateError):
    """An event sequence violates an invariant the snapshot depends on."""


ClodexStateError = OrchestratorStateError


class RunLocked(OrchestratorStateError):
    """Another process holds the ledger's session lock."""

    def __init__(self, ledger_dir, pid=None, acquired_at=None, holder_alive=None):
        self.ledger_dir = str(ledger_dir)
        self.pid = pid
        self.acquired_at = acquired_at
        self.holder_alive = holder_alive
        liveness = {True: "running", False: "not running", None: "liveness unknown"}[holder_alive]
        super().__init__(
            "ledger %s is locked by pid %s (%s) since %s"
            % (self.ledger_dir, pid, liveness, acquired_at)
        )


# --------------------------------------------------------------------------- #
# paths, schema and identity
# --------------------------------------------------------------------------- #

def events_path(ledger_dir):
    return os.path.join(str(ledger_dir), EVENTS_FILE)


def snapshot_path(ledger_dir):
    return os.path.join(str(ledger_dir), SNAPSHOT_FILE)


def lock_path(ledger_dir):
    return os.path.join(str(ledger_dir), LOCK_FILE)


def write_lock_path(ledger_dir):
    return os.path.join(str(ledger_dir), WRITE_LOCK_FILE)


def _now_iso():
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _schema_path(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


_SCHEMA_CACHE = {}


def load_schema(name="run-plan.schema.json"):
    """Load the adjacent run-plan schema, caching only the parsed JSON."""
    if name not in _SCHEMA_CACHE:
        with open(_schema_path(name), "r", encoding="utf-8") as handle:
            _SCHEMA_CACHE[name] = json.load(handle)
    return _SCHEMA_CACHE[name]


def _type_ok(value, type_name):
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "null":
        return value is None
    raise OrchestratorStateError("schema uses unsupported type %r" % type_name)


def validate(value, schema, path="$"):
    """Validate the small JSON Schema subset used by the run-plan contract.

    This intentionally follows the clodex reducer's stdlib validator, adding
    the schema features needed here: ``additionalProperties``, array bounds,
    and strings' ``pattern``.  It raises on the first problem and returns
    ``None`` on success, like the source validator.
    """
    types = schema.get("type")
    if types is not None:
        names = [types] if isinstance(types, str) else types
        if not any(_type_ok(value, name) for name in names):
            raise OrchestratorStateError(
                "%s: expected %s, got %s"
                % (path, "|".join(names), type(value).__name__)
            )
    if "enum" in schema and value not in schema["enum"]:
        raise OrchestratorStateError("%s: %r is not an allowed value" % (path, value))
    if "minLength" in schema and isinstance(value, str) and len(value) < schema["minLength"]:
        raise OrchestratorStateError("%s: string is shorter than %d" % (path, schema["minLength"]))
    if "pattern" in schema and isinstance(value, str):
        import re

        if re.search(schema["pattern"], value) is None:
            raise OrchestratorStateError("%s: string does not match required pattern" % path)
    if "minimum" in schema and isinstance(value, (int, float)) and value < schema["minimum"]:
        raise OrchestratorStateError("%s: number is below %s" % (path, schema["minimum"]))
    if "maximum" in schema and isinstance(value, (int, float)) and value > schema["maximum"]:
        raise OrchestratorStateError("%s: number is above %s" % (path, schema["maximum"]))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise OrchestratorStateError("%s: missing required field %r" % (path, key))
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise OrchestratorStateError(
                    "%s: unknown field(s) %s" % (path, ", ".join(repr(key) for key in unknown))
                )
        for key, subschema in properties.items():
            if key in value:
                validate(value[key], subschema, "%s.%s" % (path, key))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise OrchestratorStateError(
                "%s: needs at least %d item(s)" % (path, schema["minItems"])
            )
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(encoded) != len(set(encoded)):
                raise OrchestratorStateError("%s: items must be unique" % path)
        if "items" in schema:
            for index, item in enumerate(value):
                validate(item, schema["items"], "%s[%d]" % (path, index))

    # JSON Schema cannot express this cross-item identity constraint without
    # making the plan schema needlessly opaque.  It is still part of validate's
    # contract, so duplicate lane ids fail before any ledger event is opened.
    if schema.get("$id") == "lane-orchestration/run-plan.schema.json" and isinstance(value, dict):
        lanes = value.get("lanes")
        if isinstance(lanes, list):
            ids = [lane.get("id") for lane in lanes if isinstance(lane, dict)]
            if len(ids) != len(set(ids)):
                raise OrchestratorStateError("$.lanes: duplicate lane id")


def validate_run_plan(plan):
    """Validate a decoded run-plan, including duplicate lane ids."""
    validate(plan, load_schema())
    return plan


def _read_run_plan(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            plan = json.load(handle)
    except (OSError, ValueError) as exc:
        raise OrchestratorStateError("cannot read run-plan %s: %s" % (path, exc))
    validate_run_plan(plan)
    return plan


def compute_run_plan_sha(path):
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError as exc:
        raise OrchestratorStateError("cannot hash run-plan %s: %s" % (path, exc))


def ledger_dir_for(run_plan_path, ledger_root=None):
    """Return the identity-bearing default ledger path for a run-plan."""
    path = os.path.abspath(os.path.expanduser(str(run_plan_path)))
    plan = _read_run_plan(path)
    root = ledger_root
    if root is None:
        root = os.path.join(os.path.expanduser("~"), ".lane-orchestrator", "runs")
    root = os.path.abspath(os.path.expanduser(str(root)))
    return os.path.join(root, "%s-%s" % (plan["date"], compute_run_plan_sha(path)[:8]))


default_ledger_dir = ledger_dir_for
run_plan_sha = compute_run_plan_sha


# --------------------------------------------------------------------------- #
# write lock and session lock — copied disciplines
# --------------------------------------------------------------------------- #

def _flock_until(fd, ledger_dir, timeout):
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in _WOULD_BLOCK:
                raise
            if time.monotonic() >= deadline:
                raise OrchestratorStateError(
                    "timed out after %gs waiting to write %s; another writer is not finishing"
                    % (timeout, ledger_dir)
                )
            time.sleep(0.005)


@contextmanager
def _write_lock(ledger_dir, timeout=WRITE_LOCK_TIMEOUT):
    key = os.path.realpath(str(ledger_dir))
    held = _WRITE_LOCKS.get(key)
    if held is not None:
        held[1] += 1
        try:
            yield
        finally:
            held[1] -= 1
        return

    os.makedirs(key, exist_ok=True)
    fd = os.open(write_lock_path(key), os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        _flock_until(fd, key, timeout)
    except BaseException:
        os.close(fd)
        raise
    _WRITE_LOCKS[key] = [fd, 1]
    try:
        yield
    finally:
        del _WRITE_LOCKS[key]
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _read_lock(ledger_dir):
    try:
        with open(lock_path(ledger_dir), "r", encoding="utf-8") as handle:
            holder = json.load(handle)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return {}
    return holder if isinstance(holder, dict) else {}


def _holder_liveness(holder):
    """True / False / None, with unidentifiable holders treated as unknown."""
    pid = (holder or {}).get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _holds_lock(holder):
    if not holder:
        return False
    if holder.get("pid") == os.getpid():
        return True
    token = os.environ.get(LOCK_TOKEN_ENV)
    return bool(token) and holder.get("token") == token


def _locked_error(ledger_dir, holder):
    holder = holder or {}
    return RunLocked(
        ledger_dir,
        holder.get("pid"),
        holder.get("acquired_at"),
        _holder_liveness(holder),
    )


class Lock:
    """The session lock. It is re-entrant for a delegated token holder."""

    def __init__(self, ledger_dir):
        self.ledger_dir = str(ledger_dir)
        self.path = lock_path(self.ledger_dir)
        self.pid = os.getpid()
        self.acquired_at = _now_iso()
        self.token = secrets.token_hex(16)
        self._held = False
        self._restore_token = None

        os.makedirs(self.ledger_dir, exist_ok=True)
        with _write_lock(self.ledger_dir):
            try:
                fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                raise _locked_error(self.ledger_dir, _read_lock(self.ledger_dir))
            payload = {"pid": self.pid, "acquired_at": self.acquired_at, "token": self.token}
            try:
                try:
                    os.write(fd, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except BaseException:
                try:
                    os.unlink(self.path)
                except OSError:
                    pass
                raise

        self._restore_token = os.environ.get(LOCK_TOKEN_ENV)
        os.environ[LOCK_TOKEN_ENV] = self.token
        self._held = True

    def release(self):
        if not self._held:
            return
        self._held = False
        if self._restore_token is None:
            os.environ.pop(LOCK_TOKEN_ENV, None)
        else:
            os.environ[LOCK_TOKEN_ENV] = self._restore_token
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False


def acquire_lock(ledger_dir):
    return Lock(ledger_dir)


def break_lock(ledger_dir):
    """Remove a dead holder's lock; live and unknown holders always refuse."""
    if _read_lock(ledger_dir) is None:
        return None
    with _write_lock(ledger_dir):
        holder = _read_lock(ledger_dir)
        if holder is None:
            return None
        if _holder_liveness(holder) is not False:
            raise _locked_error(ledger_dir, holder)
        try:
            os.unlink(lock_path(ledger_dir))
        except FileNotFoundError:
            pass
        return holder


@contextmanager
def _writer(ledger_dir):
    if _holds_lock(_read_lock(ledger_dir)):
        with _write_lock(ledger_dir):
            yield None
        return
    lock = Lock(ledger_dir)
    try:
        with _write_lock(ledger_dir):
            yield lock
    finally:
        lock.release()


# --------------------------------------------------------------------------- #
# log reading, repair and the frozen reducer
# --------------------------------------------------------------------------- #

def _is_event_line(raw):
    try:
        return isinstance(json.loads(raw), dict)
    except (TypeError, ValueError):
        return False


def _sync_truncate(path, size):
    with open(path, "r+b") as handle:
        handle.truncate(size)
        handle.flush()
        os.fsync(handle.fileno())


def _repair_torn_tail(path):
    """Complete a parseable unterminated event or drop an invalid final line."""
    with open(path, "rb") as handle:
        data = handle.read()
    if not data:
        return
    if data.endswith(b"\n"):
        start = data.rfind(b"\n", 0, len(data) - 1) + 1
        tail = data[start:-1]
        if not tail.strip() or _is_event_line(tail):
            return
        _sync_truncate(path, start)
        _LOG.warning("dropped invalid final line in %s (%d bytes)", path, len(data) - start)
        return
    start = data.rfind(b"\n") + 1
    tail = data[start:]
    if _is_event_line(tail):
        with open(path, "ab") as handle:
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        _LOG.warning("completed unterminated final line in %s", path)
        return
    _sync_truncate(path, start)
    _LOG.warning("truncated torn final line in %s (%d bytes dropped)", path, len(data) - start)


def _read_events(ledger_dir):
    path = events_path(ledger_dir)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        lines = [line for line in handle.read().splitlines() if line.strip()]
    events = []
    for index, line in enumerate(lines):
        try:
            event = json.loads(line)
        except ValueError:
            if index == len(lines) - 1:
                _LOG.warning("dropping torn final line in %s: %.80s", path, line)
                break
            raise OrchestratorStateError("%s: line %d is not valid JSON" % (path, index + 1))
        if not isinstance(event, dict):
            raise OrchestratorStateError("%s: line %d is not a JSON object" % (path, index + 1))
        events.append(event)
    return events


def _last_seq(events):
    if not events:
        return 0
    seq = events[-1].get("seq")
    if not isinstance(seq, int) or isinstance(seq, bool):
        raise OrchestratorStateError("last event has a non-integer seq: %r" % seq)
    return seq


def _require_string(event, key, allow_null=False):
    value = event.get(key)
    if allow_null and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise _violation(event, "%s must be a non-empty string" % key)


def _require_int(event, key, minimum=0):
    value = event.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise _violation(event, "%s must be an integer >= %d" % (key, minimum))


def _violation(event, message):
    return ReducerInvariantError(
        "event %s (%s): %s" % (event.get("seq"), event.get("e"), message)
    )


def _lane(snap, lane, event):
    if lane not in snap["lanes"]:
        snap["lanes"][lane] = {
            "id": lane,
            "status": "pending",
            "last_seq": 0,
            "dispatches": [],
            "parks": [],
            "unparks": [],
        }
    return snap["lanes"][lane]


def _provider(event, stage=None):
    value = event.get("provider", event.get("kind"))
    if value is not None:
        return value
    return "codex" if (stage or event.get("stage", "")).lower().startswith("qa") else "claude"


def _recompute_dispatchable(snap):
    specs = snap.get("lane_specs") or []
    ready = []
    for spec in specs:
        lane_id = spec.get("id")
        current = snap["lanes"].get(lane_id, {}).get("status", "pending")
        if current not in ("pending", "ready", "unparked"):
            continue
        dependencies = spec.get("depends_on") or []
        if all(snap["lanes"].get(dep, {}).get("status") == "completed" for dep in dependencies):
            ready.append(lane_id)
    snap["dispatchable"] = sorted(ready)


def base_snapshot():
    return {
        "schema_version": SCHEMA_VERSION,
        "run_plan": {"path": None, "sha": None, "mode": None, "date": None},
        "lane_specs": [],
        "lanes": {},
        "receipts": {},
        "claude_legs": {},
        "gates": [],
        "budget_samples": [],
        "dispatchable": [],
        "closed": False,
        "last_seq": 0,
    }


def _on_run_opened(snap, event):
    if snap["run_plan"]["sha"] is not None:
        raise _violation(event, "the run-plan is already recorded")
    identity = event.get("run_plan") if isinstance(event.get("run_plan"), dict) else {}
    path = event.get("run_plan_path", event.get("path", identity.get("path")))
    sha = event.get("run_plan_sha", event.get("sha", identity.get("sha")))
    _require_string(event, "mode")
    if event["mode"] not in ("unattended", "morning-approval"):
        raise _violation(event, "mode must be unattended or morning-approval")
    if not isinstance(path, str) or not path.strip():
        raise _violation(event, "orch:run:opened needs run_plan_path")
    if not isinstance(sha, str) or len(sha) != 64 or not all(c in "0123456789abcdef" for c in sha):
        raise _violation(event, "orch:run:opened needs the full run-plan sha")
    snap["run_plan"] = {
        "path": path,
        "sha": sha,
        "mode": event["mode"],
        "date": event.get("date"),
    }
    specs = event.get("lanes", event.get("lane_specs", []))
    if specs:
        if not isinstance(specs, list):
            raise _violation(event, "lanes must be an array")
        seen = set()
        for spec in specs:
            if not isinstance(spec, dict) or not isinstance(spec.get("id"), str):
                raise _violation(event, "lane specs need string ids")
            if spec["id"] in seen:
                raise _violation(event, "duplicate lane id %r" % spec["id"])
            seen.add(spec["id"])
            snap["lane_specs"].append(dict(spec))
            _lane(snap, spec["id"], event)
    _recompute_dispatchable(snap)


def _on_dispatched(snap, event):
    for key in ("op_id", "lane", "stage"):
        _require_string(event, key)
    if event["op_id"] in snap["receipts"]:
        raise _violation(event, "op_id %r was already used" % event["op_id"])
    watermark = event.get("lane_last_seq", event.get("last_seq"))
    if not isinstance(watermark, int) or isinstance(watermark, bool) or watermark < 0:
        raise _violation(event, "lane_last_seq must be a non-negative integer")
    oracle = event.get("oracle", event.get("oracle_path"))
    oracle_paths = event.get("oracle_paths", event.get("oracles"))
    if oracle is None and not oracle_paths:
        raise _violation(event, "lane:dispatched needs oracle paths")
    if oracle_paths is not None and not isinstance(oracle_paths, list):
        raise _violation(event, "oracle_paths must be an array")
    if oracle is not None and not isinstance(oracle, str):
        raise _violation(event, "oracle must be a path")
    # Attempt-uniqueness is structural: every oracle path (and the marker)
    # must embed this receipt's op_id, so no receipt can be pointed at an
    # earlier attempt's artifact and settled from it.
    if _provider(event) not in ("claude", "codex"):
        raise _violation(event, "provider must be claude or codex")
    for candidate in [oracle] + list(oracle_paths or []):
        if isinstance(candidate, str) and event["op_id"] not in candidate:
            raise _violation(event, "oracle path does not embed the op_id")
    marker_path = event.get("marker")
    if marker_path is not None and (
        not isinstance(marker_path, str) or event["op_id"] not in marker_path
    ):
        raise _violation(event, "marker path does not embed the op_id")
    lane_state = _lane(snap, event["lane"], event)
    if lane_state["status"] == "parked":
        raise _violation(
            event,
            "lane %r is parked; unpark it before dispatching another attempt"
            % event["lane"],
        )
    receipt = {
        "op_id": event["op_id"],
        "lane": event["lane"],
        "stage": event["stage"],
        "provider": _provider(event),
        "status": "pending",
        "phase": "pending",
        "oracle": oracle,
        "oracle_paths": list(oracle_paths or ([oracle] if oracle else [])),
        "marker": event.get("marker"),
        "lane_last_seq": watermark,
        "dispatched_seq": event["seq"],
        "pid": None,
        "detach_line": None,
        "outcome": None,
        "envelope": None,
        "claude_leg_seq": None,
    }
    snap["receipts"][event["op_id"]] = receipt
    lane_state["dispatches"].append(event["op_id"])
    lane_state["status"] = "running"
    lane_state["last_seq"] = watermark
    _recompute_dispatchable(snap)


def _receipt(snap, event):
    op_id = event.get("op_id")
    if not isinstance(op_id, str) or op_id not in snap["receipts"]:
        raise _violation(event, "no receipt for op_id %r" % op_id)
    return snap["receipts"][op_id]


def _on_spawning(snap, event):
    receipt = _receipt(snap, event)
    if receipt["phase"] != "pending":
        raise _violation(event, "receipt %r is %s, not pending" % (receipt["op_id"], receipt["phase"]))
    receipt["phase"] = "spawning"
    receipt["status"] = "spawning"
    receipt["spawning_seq"] = event["seq"]
    receipt["spawning_t"] = event.get("t")


def _on_launched(snap, event):
    receipt = _receipt(snap, event)
    if receipt["phase"] != "spawning":
        raise _violation(event, "receipt %r is %s, not spawning" % (receipt["op_id"], receipt["phase"]))
    _require_int(event, "pid", minimum=1)
    _require_string(event, "detach_line")
    receipt["phase"] = "launched"
    receipt["status"] = "launched"
    receipt["pid"] = event["pid"]
    receipt["detach_line"] = event["detach_line"]
    receipt["launched_seq"] = event["seq"]


def _on_claude_leg(snap, event):
    receipt = _receipt(snap, event)
    if receipt["provider"] != "claude":
        raise _violation(event, "claude:leg belongs only to a Claude receipt")
    op_id = event["op_id"]
    if op_id in snap["claude_legs"]:
        raise _violation(event, "claude:leg for op_id %r already exists" % op_id)
    _require_string(event, "lane")
    if event["lane"] != receipt["lane"]:
        raise _violation(event, "claude:leg lane does not match its receipt")
    cost = event.get("cost_usd")
    if cost is not None and (
        isinstance(cost, bool) or not isinstance(cost, (int, float))
        or not math.isfinite(cost) or cost < 0
    ):
        raise _violation(event, "cost_usd must be a finite non-negative number or null")
    if not isinstance(event.get("models"), list):
        raise _violation(event, "models must be an array")
    if event.get("session_id") is not None and not isinstance(event.get("session_id"), str):
        raise _violation(event, "session_id must be a string or null")
    leg = dict(event)
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        leg["cost_usd"] = float(cost)
    snap["claude_legs"][op_id] = leg
    receipt["claude_leg_seq"] = event["seq"]


def _on_settled(snap, event):
    receipt = _receipt(snap, event)
    if receipt["phase"] == "done":
        raise _violation(event, "receipt %r is already done" % receipt["op_id"])
    outcome = event.get("outcome")
    if outcome not in ("complete", "failed", "unknown"):
        raise _violation(event, "outcome must be complete, failed, or unknown")
    envelope = event.get("envelope", event.get("envelope_path"))
    if envelope is not None and not isinstance(envelope, str):
        raise _violation(event, "envelope must be a path or null")
    if receipt["provider"] == "claude" and receipt["op_id"] not in snap["claude_legs"]:
        raise _violation(event, "receipt %r cannot be done before its claude:leg" % receipt["op_id"])
    receipt["phase"] = "done"
    receipt["status"] = "done"
    receipt["outcome"] = outcome
    receipt["envelope"] = envelope
    receipt["settled_seq"] = event["seq"]
    _recompute_dispatchable(snap)


def _on_parked(snap, event):
    _require_string(event, "lane")
    _require_string(event, "gate")
    _require_string(event, "record_path")
    watermark = event.get("lane_last_seq", event.get("last_seq"))
    if not isinstance(watermark, int) or isinstance(watermark, bool) or watermark < 0:
        raise _violation(event, "lane_last_seq must be a non-negative integer")
    lane_state = _lane(snap, event["lane"], event)
    if lane_state["status"] == "parked":
        raise _violation(event, "lane %r is already parked" % event["lane"])
    lane_state["status"] = "parked"
    lane_state["last_seq"] = watermark
    lane_state["parks"].append({
        "gate": event["gate"],
        "record_path": event["record_path"],
        "lane_last_seq": watermark,
        "seq": event["seq"],
    })
    snap["dispatchable"] = [lane for lane in snap["dispatchable"] if lane != event["lane"]]


def _on_unparked(snap, event):
    _require_string(event, "lane")
    _require_string(event, "answer_text")
    _require_string(event, "record_sha")
    lane_state = _lane(snap, event["lane"], event)
    if lane_state["status"] != "parked" or not lane_state["parks"]:
        raise _violation(event, "lane %r has no prior park" % event["lane"])
    lane_state["status"] = "unparked"
    lane_state["unparks"].append({
        "answer_text": event["answer_text"],
        "record_sha": event["record_sha"],
        "seq": event["seq"],
    })
    lane_state["last_seq"] = event["seq"]
    _recompute_dispatchable(snap)


def _on_completed(snap, event):
    _require_string(event, "lane")
    watermark = event.get("lane_last_seq", event.get("last_seq"))
    if not isinstance(watermark, int) or isinstance(watermark, bool) or watermark < 0:
        raise _violation(event, "lane_last_seq must be a non-negative integer")
    lane_state = _lane(snap, event["lane"], event)
    lane_state["status"] = "completed"
    lane_state["last_seq"] = watermark
    _recompute_dispatchable(snap)


def _on_gate(snap, event):
    if "gate" not in event and "id" in event:
        event = dict(event, gate=event["id"])
    _require_string(event, "gate")
    _require_string(event, "verdict")
    _require_string(event, "mechanism")
    lane = event.get("lane")
    if lane is not None and not isinstance(lane, str):
        raise _violation(event, "lane must be a string or null")
    snap["gates"].append({
        "id": event["gate"],
        "lane": lane,
        "verdict": event["verdict"],
        "mechanism": event["mechanism"],
        "seq": event["seq"],
    })


def _on_budget(snap, event):
    if not isinstance(event.get("windows"), dict):
        raise _violation(event, "windows must be an object")
    snap["budget_samples"].append({"windows": event["windows"], "seq": event["seq"]})


def _handlers():
    return {
        "orch:run:opened": _on_run_opened,
        "lane:dispatched": _on_dispatched,
        "lane:spawning": _on_spawning,
        "lane:launched": _on_launched,
        "lane:settled": _on_settled,
        "claude:leg": _on_claude_leg,
        "lane:parked": _on_parked,
        "lane:unparked": _on_unparked,
        "lane:completed": _on_completed,
        "gate:evaluated": _on_gate,
        "budget:sampled": _on_budget,
        "orch:run:closed": lambda snap, event: snap.update({"closed": True}),
    }


HANDLERS = _handlers()


def reduce_events(events):
    """Purely fold events into a deterministic snapshot."""
    snap = base_snapshot()
    for event in events:
        if not isinstance(event, dict):
            raise OrchestratorStateError("event log contains a non-object")
        name = event.get("e")
        handler = HANDLERS.get(name)
        if handler is None:
            raise OrchestratorStateError("event %s: unknown event type %r" % (event.get("seq"), name))
        seq = event.get("seq")
        if not isinstance(seq, int) or isinstance(seq, bool) or seq <= snap["last_seq"]:
            raise OrchestratorStateError(
                "event log seq is not monotonic: %r follows %r" % (seq, snap["last_seq"])
            )
        handler(snap, event)
        snap["last_seq"] = seq
    _recompute_dispatchable(snap)
    return snap


# --------------------------------------------------------------------------- #
# identity, append and derived snapshot
# --------------------------------------------------------------------------- #

def _stamp(event, seq, timestamp):
    record = dict(event)
    record["schema_version"] = SCHEMA_VERSION
    record["seq"] = seq
    record.setdefault("t", timestamp)
    if not isinstance(record.get("e"), str) or record["e"] not in EVENT_TYPES:
        raise OrchestratorStateError("event has unknown type %r" % record.get("e"))
    return record


def _identity_error(ledger_dir, events, candidate, run_plan_path=None, run_plan_sha_value=None):
    current = reduce_events(events)
    recorded = current["run_plan"]
    candidate_open = candidate.get("e") == "orch:run:opened"
    supplied_path = run_plan_path
    supplied_sha = run_plan_sha_value
    if supplied_path is not None:
        supplied_path = os.path.abspath(os.path.expanduser(str(supplied_path)))

    if recorded["sha"] is None:
        if not candidate_open:
            return "ledger has no orch:run:opened identity; append the run-plan opening event first"
        identity = candidate.get("run_plan") if isinstance(candidate.get("run_plan"), dict) else {}
        candidate_path = candidate.get(
            "run_plan_path", candidate.get("path", identity.get("path"))
        )
        candidate_sha = candidate.get("run_plan_sha", candidate.get("sha", identity.get("sha")))
        if supplied_path is not None:
            if not isinstance(candidate_path, str) or os.path.realpath(
                os.path.abspath(os.path.expanduser(candidate_path))
            ) != os.path.realpath(supplied_path):
                return "orch:run:opened path does not match the invoked run-plan path"
        path = supplied_path or candidate_path
        if not isinstance(path, str) or not path:
            return "orch:run:opened needs a run-plan path"
        path = os.path.abspath(os.path.expanduser(path))
        try:
            actual = run_plan_sha(path)
        except OrchestratorStateError as exc:
            return str(exc)
        expected = supplied_sha or candidate_sha
        if expected != actual:
            return "run-plan sha mismatch: event records %s, file is %s" % (expected, actual)
        if not isinstance(expected, str) or len(expected) != 64:
            return "orch:run:opened must record the full run-plan sha"
        # The sha alone does not stop an opening event from recording
        # substituted scheduling content beside a truthful hash: the event's
        # mode/date/lanes must BE the hashed file's.
        try:
            plan = _read_run_plan(path)
        except OrchestratorStateError as exc:
            return str(exc)
        if candidate.get("mode") != plan.get("mode"):
            return "orch:run:opened mode does not match the hashed run-plan"
        if candidate.get("date") not in (None, plan.get("date")):
            return "orch:run:opened date does not match the hashed run-plan"
        event_lanes = candidate.get("lanes", candidate.get("lane_specs"))
        if event_lanes not in (None, [], plan.get("lanes")):
            return "orch:run:opened lanes do not match the hashed run-plan"
        candidate["run_plan_path"] = path
        candidate["run_plan_sha"] = expected
        candidate.pop("path", None)
        candidate.pop("sha", None)
        return None

    path = supplied_path or recorded["path"]
    if not path:
        return "ledger identity has no run-plan path"
    try:
        actual = run_plan_sha(path)
    except OrchestratorStateError as exc:
        return str(exc)
    expected = supplied_sha or actual
    if actual != expected or actual != recorded["sha"]:
        return (
            "run-plan sha mismatch for ledger %s: recorded %s, invoked %s"
            % (ledger_dir, recorded["sha"], expected)
        )
    if os.path.realpath(path) != os.path.realpath(recorded["path"]):
        return "run-plan path mismatch: ledger records %s, invoked %s" % (recorded["path"], path)
    return None


def check_ledger_identity(ledger_dir, run_plan_path=None, run_plan_sha=None):
    """Return a refusal string when a ledger is not bound to the invoked plan."""
    events = _read_events(ledger_dir)
    if not events:
        return "ledger has no orch:run:opened identity"
    return _identity_error(
        ledger_dir,
        events,
        {"e": "budget:sampled", "seq": _last_seq(events) + 1},
        run_plan_path,
        run_plan_sha,
    )


_check_ledger_identity = check_ledger_identity


def append_event(ledger_dir, event, run_plan_path=None, run_plan_sha=None, internal=False):
    """Append one event durably after reducing log plus candidate.

    ``internal`` is reserved for ``settle``: a Claude leg is a receipt join,
    not a free-standing external append.  The event remains ordinary JSON in
    the log, so replay never depends on process-local flags.
    """
    if not isinstance(event, dict):
        raise OrchestratorStateError("event must be a JSON object, got %s" % type(event).__name__)
    if not event.get("e"):
        raise OrchestratorStateError("event is missing its 'e' (event type) field")
    if event.get("e") == "claude:leg" and not internal:
        raise OrchestratorStateError("claude:leg is appended by settle, not directly")

    ledger_dir = str(ledger_dir)
    path = events_path(ledger_dir)
    with _writer(ledger_dir):
        created = not os.path.exists(path)
        events = [] if created else _read_events(ledger_dir)
        seq = _last_seq(events) + 1
        record = _stamp(event, seq, _now_iso())
        problem = _identity_error(
            ledger_dir, events, record, run_plan_path, run_plan_sha
        )
        if problem is not None:
            raise OrchestratorStateError(problem)
        # Reduce before repairing or appending. A refusal must not even repair
        # a torn tail as a side effect of the rejected candidate.
        reduce_events(events + [record])
        if not created:
            _repair_torn_tail(path)
        line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        if created:
            _fsync_dir(ledger_dir)
    return seq


def rebuild(ledger_dir):
    return reduce_events(_read_events(ledger_dir))


def _validate_snapshot(snap):
    """Validate the derived snapshot before it can be written or trusted."""
    if not isinstance(snap, dict):
        raise OrchestratorStateError("snapshot is not a state object")
    required = (
        "schema_version", "run_plan", "lane_specs", "lanes", "receipts",
        "claude_legs", "gates", "budget_samples", "dispatchable", "closed", "last_seq",
    )
    missing = [key for key in required if key not in snap]
    if missing:
        raise OrchestratorStateError("snapshot is missing required field(s): %s" % ", ".join(missing))
    if snap["schema_version"] != SCHEMA_VERSION:
        raise OrchestratorStateError("snapshot schema_version is %r" % snap["schema_version"])
    if not isinstance(snap["run_plan"], dict):
        raise OrchestratorStateError("snapshot run_plan is not an object")
    for key in ("path", "sha", "mode", "date"):
        if key not in snap["run_plan"]:
            raise OrchestratorStateError("snapshot run_plan is missing %r" % key)
    if not isinstance(snap["lane_specs"], list) or not isinstance(snap["lanes"], dict):
        raise OrchestratorStateError("snapshot lane state has the wrong shape")
    if not isinstance(snap["receipts"], dict) or not isinstance(snap["claude_legs"], dict):
        raise OrchestratorStateError("snapshot receipt state has the wrong shape")
    if not isinstance(snap["gates"], list) or not isinstance(snap["budget_samples"], list):
        raise OrchestratorStateError("snapshot audit state has the wrong shape")
    if not isinstance(snap["dispatchable"], list) or not isinstance(snap["closed"], bool):
        raise OrchestratorStateError("snapshot scheduling state has the wrong shape")
    if not isinstance(snap["last_seq"], int) or isinstance(snap["last_seq"], bool) or snap["last_seq"] < 0:
        raise OrchestratorStateError("snapshot last_seq is not a non-negative integer")


def atomic_write_snapshot(ledger_dir, snap):
    _validate_snapshot(snap)
    with _writer(ledger_dir):
        os.makedirs(ledger_dir, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".run-", suffix=".json", dir=ledger_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(snap, handle, sort_keys=True, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, snapshot_path(ledger_dir))
        except BaseException:
            if os.path.exists(temp):
                os.unlink(temp)
            raise
        _fsync_dir(ledger_dir)


def load_snapshot(ledger_dir):
    path = snapshot_path(ledger_dir)
    if not os.path.exists(path):
        return rebuild(ledger_dir)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            snap = json.load(handle)
        _validate_snapshot(snap)
    except (OSError, ValueError, OrchestratorStateError) as exc:
        _LOG.warning("snapshot %s is unusable (%s); rebuilding from events", path, exc)
        return rebuild(ledger_dir)
    logged = _last_seq(_read_events(ledger_dir))
    if snap.get("last_seq") != logged:
        _LOG.warning(
            "snapshot %s is stale (last_seq %s, log %s); rebuilding from events",
            path, snap.get("last_seq"), logged,
        )
        return rebuild(ledger_dir)
    return snap


# --------------------------------------------------------------------------- #
# receipt creation, settling and recovery
# --------------------------------------------------------------------------- #

def _safe_component(value, label):
    if not isinstance(value, str) or not value or value in (".", "..") or "/" in value:
        raise OrchestratorStateError("%s must be a single non-empty path component" % label)
    return value


def mint_op_id():
    return secrets.token_hex(16)


def oracle_for(ledger_dir, lane, stage, op_id, provider="claude"):
    lane = _safe_component(lane, "lane")
    stage = _safe_component(stage, "stage")
    op_id = _safe_component(op_id, "op_id")
    if provider == "codex" or stage.lower().startswith("qa"):
        return os.path.join(str(ledger_dir), "qa", op_id)
    return os.path.join(str(ledger_dir), "lanes", lane, "%s.%s.envelope.json" % (stage, op_id))


def marker_for(ledger_dir, lane, stage, op_id, provider="claude"):
    oracle = oracle_for(ledger_dir, lane, stage, op_id, provider)
    if os.path.isdir(oracle) or stage.lower().startswith("qa"):
        return os.path.join(str(ledger_dir), "qa", "%s.started" % op_id)
    return oracle[:-len(".envelope.json")] + ".started"


def create_receipt(
    ledger_dir, lane, stage, lane_last_seq=0, provider="claude", op_id=None, oracle=None
):
    """Mint an op id, derive its oracle, and append the pending receipt."""
    op_id = op_id or mint_op_id()
    oracle = oracle or oracle_for(ledger_dir, lane, stage, op_id, provider)
    marker = marker_for(ledger_dir, lane, stage, op_id, provider)
    append_event(
        ledger_dir,
        {
            "e": "lane:dispatched",
            "op_id": op_id,
            "lane": lane,
            "stage": stage,
            "provider": provider,
            "oracle": oracle,
            "oracle_paths": [oracle],
            "marker": marker,
            "lane_last_seq": lane_last_seq,
        },
    )
    return op_id


dispatch_receipt = create_receipt


def mark_spawning(ledger_dir, op_id):
    """The fsync fence: call immediately before the wrapper's Popen."""
    return append_event(ledger_dir, {"e": "lane:spawning", "op_id": op_id})


def mark_launched(ledger_dir, op_id, pid, detach_line):
    return append_event(
        ledger_dir,
        {"e": "lane:launched", "op_id": op_id, "pid": pid, "detach_line": detach_line},
    )


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _oracle_envelope(receipt):
    oracle = receipt.get("oracle")
    if not oracle:
        paths = receipt.get("oracle_paths") or []
        oracle = paths[0] if paths else None
    if not oracle:
        return False, None, None
    if os.path.isdir(oracle):
        try:
            paths = sorted(
                os.path.join(root, name)
                for root, _dirs, files in os.walk(oracle)
                for name in files
                if name.endswith(".envelope.json")
            )
        except OSError:
            paths = []
        for path in paths:
            value = _read_json(path)
            if value is not None:
                return True, value, path
        return bool(paths), None, paths[0] if paths else None
    if not os.path.exists(oracle):
        return False, None, oracle
    return True, _read_json(oracle), oracle


def _envelope_outcome(value):
    """Map an envelope to complete/failed/unknown across BOTH real shapes.

    A `claude -p --output-format json` envelope reports through `is_error`
    (plus subtype/terminal_reason); it has no `status` field, and reading one
    as unknown settled every successful Claude dispatch as unresolved and
    nulled its real cost.  Runner (Codex QA) envelopes carry `status`.
    """
    if not isinstance(value, dict):
        return "unknown"
    if "is_error" in value:
        if value.get("is_error") is False:
            return "complete"
        if value.get("is_error") is True:
            return "failed"
        return "unknown"
    status = value.get("status", value.get("outcome"))
    if status in ("complete", "success", "succeeded"):
        return "complete"
    if status in ("failed", "failure", "partial", "interrupted"):
        return "failed"
    return "unknown"


def _leg_from_envelope(receipt, value, outcome, never_spawned=False):
    cost = None
    models = []
    session_id = None
    if isinstance(value, dict):
        raw_cost = value.get("total_cost_usd")
        if isinstance(raw_cost, (int, float)) and not isinstance(raw_cost, bool) and math.isfinite(raw_cost) and raw_cost >= 0:
            cost = float(raw_cost)
        raw_models = value.get("models")
        if isinstance(raw_models, list):
            models = list(raw_models)
        elif isinstance(value.get("modelUsage"), dict):
            models = sorted(value["modelUsage"])
        session_id = value.get("session_id")
        if session_id is not None and not isinstance(session_id, str):
            session_id = None
    if outcome == "unknown":
        cost = None
    if never_spawned:
        # An affirmative negative proves the model never ran: the spend is a
        # known ZERO, not an unknown that would fail budget gates forever.
        cost = 0.0
        models = []
        session_id = None
    return {
        "e": "claude:leg",
        "op_id": receipt["op_id"],
        "lane": receipt["lane"],
        "cost_usd": cost,
        "models": models,
        "session_id": session_id,
        "outcome": outcome,
    }


def settle(
    ledger_dir, op_id, outcome=None,
    run_plan_path=None, run_plan_sha=None, never_spawned=False,
):
    """Idempotently join the envelope cost, then mark the receipt done.

    The envelope is read ONLY through the receipt's own oracle — there is no
    caller-supplied envelope override, so a fresh op_id can never be settled
    from another attempt's artifact.  When the oracle parses, an explicit
    `outcome` may only downgrade to "unknown" (the park path); it can never
    contradict what the envelope says.  `never_spawned` marks the affirmative
    negative: the leg records a known zero cost, not an unknown.
    """
    snap = rebuild(ledger_dir)
    receipt = snap["receipts"].get(op_id)
    if receipt is None:
        raise OrchestratorStateError("no receipt for op_id %r" % op_id)
    if receipt["phase"] == "done":
        return receipt

    present, value, found_path = _oracle_envelope(receipt)
    derived = _envelope_outcome(value) if (present and value is not None) else None
    if never_spawned:
        if present and value is not None:
            raise OrchestratorStateError(
                "receipt %r has an envelope; it cannot be settled never-spawned" % op_id
            )
        outcome = "failed"
    elif outcome is None:
        outcome = derived if derived is not None else "unknown"
    elif derived is not None and outcome != derived and outcome != "unknown":
        raise OrchestratorStateError(
            "outcome %r contradicts the oracle envelope's %r" % (outcome, derived)
        )
    if outcome not in ("complete", "failed", "unknown"):
        raise OrchestratorStateError("outcome must be complete, failed, or unknown")

    if receipt["provider"] == "claude" and op_id not in snap["claude_legs"]:
        append_event(
            ledger_dir,
            _leg_from_envelope(receipt, value, outcome, never_spawned=never_spawned),
            run_plan_path=run_plan_path,
            run_plan_sha=run_plan_sha,
            internal=True,
        )
        snap = rebuild(ledger_dir)
        receipt = snap["receipts"][op_id]

    append_event(
        ledger_dir,
        {
            "e": "lane:settled",
            "op_id": op_id,
            "outcome": outcome,
            "envelope": found_path if present else None,
        },
        run_plan_path=run_plan_path,
        run_plan_sha=run_plan_sha,
    )
    return rebuild(ledger_dir)["receipts"][op_id]


def _process_table_pids(op_id):
    """Find the wrapper by argv without spawning ``ps`` or another helper.

    Returns a sorted pid list when the table was scannable, and ``None`` when
    it is UNAVAILABLE — macOS has no ``/proc``, and an unavailable table must
    never read as "nothing is running": that turned a live dispatch into an
    affirmative negative on the primary platform.
    """
    proc = "/proc"
    try:
        entries = os.listdir(proc)
    except OSError:
        return None
    found = []
    for name in entries:
        if not name.isdigit():
            continue
        try:
            with open(os.path.join(proc, name, "cmdline"), "rb") as handle:
                command = handle.read().replace(b"\0", b" ")
        except OSError:
            continue
        if op_id.encode("utf-8") in command:
            found.append(int(name))
    return sorted(found)


def _pid_alive(pid):
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def _iso_to_epoch(text):
    if not isinstance(text, str):
        return None
    try:
        parsed = _datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_datetime.timezone.utc)
    return parsed.timestamp()


#: How long after the fsynced ``lane:spawning`` fence a wrapper is allowed to
#: not yet have written its marker before a missing marker counts as an
#: affirmative negative on a platform whose process table cannot be scanned.
RECONCILE_SPAWN_GRACE_SECONDS = 30.0


def reconcile(ledger_dir, process_pids=None, run_plan_path=None, run_plan_sha=None):
    """Resolve every open receipt, stopping at unknown reality.

    Return records are intentionally useful to the CLI and tests.  A pending
    receipt with no spawning marker is the only one labelled ``safe_to_replan``.
    A started attempt with no envelope is parked, never silently re-dispatched.
    """
    problem = check_ledger_identity(ledger_dir, run_plan_path, run_plan_sha)
    if problem is not None:
        raise OrchestratorStateError(problem)
    results = []

    def park(op_id, lane, record_path, reason):
        now = rebuild(ledger_dir)
        if now["lanes"].get(lane, {}).get("status") != "parked":
            append_event(
                ledger_dir,
                {
                    "e": "lane:parked",
                    "lane": lane,
                    "gate": "reconcile:%s" % op_id,
                    "record_path": record_path,
                    "lane_last_seq": now["last_seq"],
                },
            )
        results.append({"op_id": op_id, "state": "PARK", "reason": reason})

    for op_id, receipt in list(rebuild(ledger_dir)["receipts"].items()):
        if receipt["phase"] == "done":
            # Repair the crash window between an unknown settle and its park:
            # a done-unknown receipt whose lane is not parked must not read as
            # resolved (a later reconcile would otherwise skip it forever).
            if receipt.get("outcome") == "unknown":
                lane_status = rebuild(ledger_dir)["lanes"].get(receipt["lane"], {}).get("status")
                if lane_status != "parked":
                    park(op_id, receipt["lane"],
                         receipt.get("envelope") or receipt.get("marker") or "-",
                         "repair: unknown outcome without a park")
            continue
        if receipt["phase"] == "pending":
            results.append({"op_id": op_id, "state": "safe_to_replan"})
            continue

        pids = process_pids(op_id) if callable(process_pids) else _process_table_pids(op_id)
        # Liveness is a tri-state. A scannable-but-empty table (pids == [])
        # still consults the recorded pid: Codex QA carries its op_id in the
        # runner's ENVIRONMENT, not its argv, so an argv scan misses a live
        # detached QA attempt on Linux too.
        alive = bool(pids)
        if not alive:
            pid_state = _pid_alive(receipt.get("pid"))
            if pid_state is True:
                alive = True
            elif pids is None and pid_state is None:
                alive = None
        if alive:
            adopted_pid = pids[0] if pids else receipt.get("pid")
            if receipt["phase"] == "spawning" and pids:
                mark_launched(ledger_dir, op_id, pids[0], "adopted process pid %d" % pids[0])
            results.append({"op_id": op_id, "state": "adopted", "pid": adopted_pid})
            continue

        marker = receipt.get("marker")
        present, value, path = _oracle_envelope(receipt)
        if present and value is not None:
            final = _envelope_outcome(value)
            settle(
                ledger_dir, op_id, outcome=final,
                run_plan_path=run_plan_path, run_plan_sha=run_plan_sha,
            )
            if final == "unknown":
                park(op_id, receipt["lane"], path or "-",
                     "envelope present but its outcome is unknown")
            else:
                results.append({"op_id": op_id, "state": "settled", "outcome": final})
            continue

        if receipt.get("provider") != "claude":
            # A Codex QA attempt has no wrapper marker: the runner writes no
            # .started file, so marker absence proves nothing. Not alive and
            # no envelope is an unknown outcome — park, never a negative.
            settle(
                ledger_dir, op_id, outcome="unknown",
                run_plan_path=run_plan_path, run_plan_sha=run_plan_sha,
            )
            park(op_id, receipt["lane"], path or marker or "-",
                 "codex attempt not running and left no envelope")
            continue

        if present and value is None:
            # An oracle file that exists but is not parseable proves neither
            # completion nor non-execution: the same unknown as a started
            # wrapper with no envelope.
            marker = marker or path
        if not marker or not os.path.exists(marker):
            # The fsynced spawning event exists, but the wrapper's own durable
            # pre-Popen marker does not. On a scannable table (alive is False)
            # this attempt provably never called a model — an affirmative
            # negative. On an UNAVAILABLE table with no usable pid, absence is
            # unprovable: only after the spawn grace may a missing marker
            # count as negative.
            if alive is None:
                spawned_at = _iso_to_epoch(receipt.get("spawning_t"))
                age = None if spawned_at is None else time.time() - spawned_at
                if age is None or age <= RECONCILE_SPAWN_GRACE_SECONDS:
                    results.append({
                        "op_id": op_id, "state": "waiting",
                        "reason": "process table unavailable; within spawn grace",
                    })
                    continue
            settle(
                ledger_dir, op_id,
                run_plan_path=run_plan_path, run_plan_sha=run_plan_sha,
                never_spawned=True,
            )
            results.append({"op_id": op_id, "state": "negative", "reason": "never spawned"})
            continue

        settle(
            ledger_dir, op_id, outcome="unknown",
            run_plan_path=run_plan_path, run_plan_sha=run_plan_sha,
        )
        park(op_id, receipt["lane"], path or marker, "started without envelope")
    return results


# --------------------------------------------------------------------------- #
# convenience operations and CLI
# --------------------------------------------------------------------------- #

def open_run(run_plan_path, ledger_dir=None):
    path = os.path.abspath(os.path.expanduser(str(run_plan_path)))
    plan = _read_run_plan(path)
    ledger_dir = ledger_dir or ledger_dir_for(path)
    append_event(
        ledger_dir,
        {
            "e": "orch:run:opened",
            "run_plan_path": path,
            "run_plan_sha": compute_run_plan_sha(path),
            "mode": plan["mode"],
            "date": plan["date"],
            "lanes": plan["lanes"],
        },
        run_plan_path=path,
    )
    return ledger_dir


def unpark(ledger_dir, lane, answer_text, record_path=None, record_sha=None):
    """Record a human answer to a park and return the resulting snapshot.

    The orchestrator command owns the park-file editing interface.  This
    helper owns the durable transition: when given a record path it binds the
    answer to the file bytes, so a later edit cannot masquerade as the answer
    that reopened the lane.
    """
    lane = _safe_component(lane, "lane")
    if record_sha is None:
        if not record_path:
            raise OrchestratorStateError("unpark needs the park record path or its sha")
        try:
            with open(record_path, "rb") as handle:
                record_sha = hashlib.sha256(handle.read()).hexdigest()
        except OSError as exc:
            raise OrchestratorStateError("cannot hash park record %s: %s" % (record_path, exc))
    append_event(
        ledger_dir,
        {
            "e": "lane:unparked",
            "lane": lane,
            "answer_text": answer_text,
            "record_sha": record_sha,
        },
    )
    return rebuild(ledger_dir)


def _cmd_append(args):
    raw = args.event if args.event is not None else sys.stdin.read()
    source = "-e payload" if args.event is not None else "stdin"
    try:
        event = json.loads(raw)
    except ValueError as exc:
        raise OrchestratorStateError("%s is not a valid JSON event: %s" % (source, exc))
    if not isinstance(event, dict):
        raise OrchestratorStateError("%s must hold one JSON object" % source)
    seq = append_event(args.ledger_dir, event, run_plan_path=args.run_plan)
    try:
        atomic_write_snapshot(args.ledger_dir, rebuild(args.ledger_dir))
    except (OrchestratorStateError, OSError) as exc:
        print(
            "lane-orchestrator-state: event %d is durably in the log but run.json was not "
            "refreshed (%s). Do not retry the append; rebuild reports true state."
            % (seq, exc),
            file=sys.stderr,
        )
        return EXIT_PARTIAL
    print(seq)
    return EXIT_OK


def _cmd_rebuild(args):
    print(json.dumps(rebuild(args.ledger_dir), sort_keys=True, indent=2))
    return EXIT_OK


def _cmd_status(args):
    snap = load_snapshot(args.ledger_dir)
    plan = snap["run_plan"]
    print("run-plan:  %s (%s)" % (plan["path"] or "-", plan["sha"] or "-"))
    print("mode:      %s   last_seq %d" % (plan["mode"] or "-", snap["last_seq"]))
    print("lanes:     %d (%d dispatchable)" % (len(snap["lanes"]), len(snap["dispatchable"])))
    print("receipts:  %d (%d open)" % (
        len(snap["receipts"]),
        sum(1 for receipt in snap["receipts"].values() if receipt["phase"] != "done"),
    ))
    print("claude:    %d leg(s)" % len(snap["claude_legs"]))
    if snap.get("closed"):
        print("closed:    yes")
    holder = _read_lock(args.ledger_dir)
    if holder is not None:
        liveness = {True: "running", False: "not running", None: "liveness unknown"}
        print("lock:      held by pid %s (%s) since %s" % (
            holder.get("pid"), liveness[_holder_liveness(holder)], holder.get("acquired_at"),
        ))
    return EXIT_OK


def _cmd_reconcile(args):
    results = reconcile(args.ledger_dir, run_plan_path=args.run_plan)
    atomic_write_snapshot(args.ledger_dir, rebuild(args.ledger_dir))
    for result in results:
        if result["state"] == "safe_to_replan":
            print("%s SAFE TO REPLAN — no spawning event" % result["op_id"])
        elif result["state"] == "PARK":
            print("%s PARK — %s" % (result["op_id"], result["reason"]))
        else:
            print("%s %s%s" % (
                result["op_id"], result["state"],
                " (%s)" % result.get("outcome") if result.get("outcome") else "",
            ))
    return EXIT_OK


def _cmd_unlock(args):
    holder = break_lock(args.ledger_dir)
    if holder is None:
        print("no lock held")
    else:
        print("removed lock held by pid %s since %s" % (holder.get("pid"), holder.get("acquired_at")))
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(
        prog="orchestrator_state.py",
        description="Read and write lane-orchestrator state. Event payloads arrive on stdin.",
        epilog="exit codes: 0 ok; 1 refused, nothing written; 2 usage; "
               "3 append only — event logged but run.json not refreshed, do not retry.",
    )
    subcommands = parser.add_subparsers(dest="command")
    for name, handler, help_text in (
        ("append", _cmd_append, "append one JSON event read from stdin; prints its assigned seq"),
        ("rebuild", _cmd_rebuild, "print the snapshot rebuilt from the event log"),
        ("status", _cmd_status, "print a short ledger summary"),
        ("reconcile", _cmd_reconcile, "resolve open receipts through their reality oracles"),
        ("unlock", _cmd_unlock, "remove the session lock of a holder that is no longer running"),
    ):
        sub = subcommands.add_parser(name, help=help_text)
        sub.add_argument("ledger_dir", help="the ledger directory")
        if name in ("append", "reconcile"):
            sub.add_argument("--run-plan", help="the run-plan path whose identity must match the ledger")
        if name == "append":
            sub.add_argument("-e", "--event", metavar="JSON", help="event JSON instead of stdin")
        sub.set_defaults(handler=handler)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_usage(sys.stderr)
        return EXIT_USAGE
    try:
        return args.handler(args)
    except (OrchestratorStateError, OSError) as exc:
        print("lane-orchestrator-state: %s" % exc, file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="lane-orchestrator-state: %(message)s")
    sys.exit(main())
