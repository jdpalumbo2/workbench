#!/usr/bin/env python3
"""Durably mark and supervise exactly one lane-stage child process.

The operation id stays in this process's argv for its entire lifetime, which
lets the state engine reconcile a crash with a process-table scan.  The marker
is a sibling of the envelope, not a child of it: it is created and fsync'd
before the only ``Popen`` call.  The child writes stdout to the attempt's
envelope, which is fsync'd after the child exits.  This wrapper deliberately
does not ``exec`` over itself; supervision is the point.

Stdlib only.  Invocation shape:

    dispatch_wrapper.py --op-id ID --marker PATH --envelope PATH -- COMMAND ...
"""

import argparse
import os
import subprocess
import sys


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _makedirs_durable(path):
    """Create a directory hierarchy and fsync every newly created level.

    ``os.makedirs`` + fsync of only the leaf persists the marker's entry in
    the leaf but not the new leaf's entry in ITS parent: after a power loss
    the whole marker path can vanish while the fsynced spawning receipt
    survives, and recovery would then double-dispatch. Each created directory
    and the pre-existing parent above the topmost creation are all fsynced.
    """
    path = os.path.abspath(path)
    missing = []
    probe = path
    while probe and not os.path.isdir(probe):
        missing.append(probe)
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    os.makedirs(path, exist_ok=True)
    for created in missing:
        _fsync_dir(created)
    if missing:
        _fsync_dir(os.path.dirname(missing[-1]) or "/")


def build_parser():
    parser = argparse.ArgumentParser(description="mark and supervise one dispatch child")
    parser.add_argument("--op-id", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--envelope", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.command or args.command[0] != "--":
        print("dispatch-wrapper: command must follow --", file=sys.stderr)
        return 2
    command = args.command[1:]
    if not command:
        print("dispatch-wrapper: command after -- is empty", file=sys.stderr)
        return 2

    marker_parent = os.path.dirname(os.path.abspath(args.marker)) or "."
    envelope_parent = os.path.dirname(os.path.abspath(args.envelope)) or "."
    _makedirs_durable(marker_parent)
    _makedirs_durable(envelope_parent)
    try:
        fd = os.open(args.marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print("dispatch-wrapper: marker already exists: %s" % args.marker, file=sys.stderr)
        return 1
    try:
        os.write(fd, ("started %s\n" % args.op_id).encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(marker_parent)

    try:
        with open(args.envelope, "wb") as envelope:
            child = subprocess.Popen(command, stdout=envelope)
            return_code = child.wait()
            envelope.flush()
            os.fsync(envelope.fileno())
    except OSError as exc:
        print("dispatch-wrapper: child could not be supervised: %s" % exc, file=sys.stderr)
        return 1
    return return_code


if __name__ == "__main__":
    sys.exit(main())
