#!/usr/bin/env python3
"""ci/matrix.py - emit the anda build matrix for halcyon-packages.

Replaces copr/submit.py's selection logic and produces output in the same
`build_matrix=<json>` shape as `anda ci` (terrapkg/packages autobuild.yml), so
the workflow stays terra-shaped. Entries: {"pkg": "anda/<name>", "arch":
"x86_64", "labels": {}}.

Selection semantics (copied from copr/submit.py --since):

  --since REV   every package whose anda/<name>/ directory changed since REV,
                plus every package in a higher batch (a changed lower batch
                may invalidate dependents). Touches under ci/, mock/,
                .github/builder/ or the root anda.hcl rebuild everything.
  no --since    the whole registry (first submission / manual full runs).

Batch numbers come from ci/packages.toml, which stays the dependency-order
registry: packages in one batch must never depend on each other, batch N may
BuildRequire batch < N output (the buildroot carries the published repo).

Usage:
  ci/matrix.py [--since REV] [--batch N ...] [--list] [--label LABEL=VALUE]

With --label each emitted entry carries extra labels (the workflow uses
labels.batch to wave the matrix). Without --list the script prints
`build_matrix=...` on stdout, exactly like `anda ci`, plus `batches=N M ...`
so the workflow knows which waves exist without re-parsing the JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGES_FILE = REPO_ROOT / "ci" / "packages.toml"
# Paths whose changes invalidate every package (infrastructure).
INFRA_PREFIXES = ("ci/", "mock/", ".github/builder/", "andax/")
INFRA_FILES = ("anda.hcl",)
ARCH = "x86_64"


def die(msg: str) -> None:
    print(f"matrix.py: error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def git_lines(*args: str) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def load_packages() -> dict[str, dict]:
    with open(PACKAGES_FILE, "rb") as fh:
        data = tomllib.load(fh)
    pkgs: dict[str, dict] = {}
    for name, entry in data.items():
        if not (REPO_ROOT / "anda" / name / f"{name}.spec").is_file():
            die(f"[{name}]: anda/{name}/{name}.spec does not exist")
        if not (REPO_ROOT / "anda" / name / "anda.hcl").is_file():
            die(f"[{name}]: anda/{name}/anda.hcl does not exist")
        pkgs[name] = {"batch": int(entry.get("batch", 0))}
    if not pkgs:
        die(f"{PACKAGES_FILE}: no packages defined")
    depths = sorted({meta["batch"] for meta in pkgs.values()})
    if depths != list(range(len(depths))):
        die(f"{PACKAGES_FILE}: batches must be contiguous starting at 0, got {depths}")
    return pkgs


def select(
    pkgs: dict[str, dict],
    only: list[str] | None,
    batches: list[int] | None,
    since: str | None,
) -> set[str]:
    """Resolve --only / --batch / --since into the package names to build."""
    if only and since:
        die("--only and --since are mutually exclusive")

    if since:
        chosen = select_since(pkgs, since)
    else:
        chosen = set(pkgs)
    if only:
        unknown = sorted(set(only) - set(pkgs))
        if unknown:
            die(f"not in {PACKAGES_FILE}: {', '.join(unknown)}")
        chosen &= set(only)
    if batches:
        chosen &= {n for n, meta in pkgs.items() if meta["batch"] in batches}
    return chosen


def select_since(pkgs: dict[str, dict], rev: str) -> set[str]:
    """Changed packages since REV, plus everything in a later batch.

    A later batch may have been built against the changed package, so it is
    rebuilt too (copr/submit.py's documented cascade semantics).
    """
    paths = git_lines("diff", "--name-only", f"{rev}..HEAD")
    if not paths:
        print(f"no file changes in {rev}..HEAD", flush=True)
        return set()
    infra = any(
        any(p.startswith(pref) for pref in INFRA_PREFIXES) or p in INFRA_FILES
        for p in paths
    )
    dirs = {
        p.split("/")[1]
        for p in paths
        if p.startswith("anda/") and len(p.split("/")) > 2
    }
    dirs = {d for d in dirs if d in pkgs}
    if infra or not dirs:
        print(
            f"{'infrastructure changed' if infra else 'no registered package changed'}"
            f" in {rev}..HEAD -> all packages",
            flush=True,
        )
        return set(pkgs)
    floor = min(pkgs[name]["batch"] for name in dirs)
    selected = {n for n, meta in pkgs.items() if meta["batch"] >= floor}
    print(
        f"changed since {rev[:12]}: {', '.join(sorted(dirs))}"
        f" -> rebuilding batches >= {floor} ({len(selected)} packages)",
        flush=True,
    )
    return selected


def entries(names: set[str], pkgs: dict[str, dict], labels: dict[str, str]):
    for name in sorted(names):
        yield {
            "pkg": f"anda/{name}",
            "arch": ARCH,
            "labels": {"batch": str(pkgs[name]["batch"]), **labels},
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--since", help="git revision; build everything changed since it")
    ap.add_argument("--only", nargs="*", help="build only these packages")
    ap.add_argument("--batch", nargs="*", type=int, help="build only these batch numbers")
    ap.add_argument(
        "--label", action="append", default=[],
        help="add LABEL=VALUE to every matrix entry (repeatable)",
    )
    ap.add_argument("--list", action="store_true", help="print a table and exit")
    args = ap.parse_args()

    pkgs = load_packages()
    chosen = select(pkgs, args.only, args.batch, args.since)
    if not chosen:
        print("matrix.py: nothing to build")
        return

    if args.list:
        for name in sorted(chosen, key=lambda n: (pkgs[n]["batch"], n)):
            print(f"{pkgs[name]['batch']}  {name}")
        return

    labels = dict(kv.split("=", 1) for kv in args.label)
    matrix = list(entries(chosen, pkgs, labels))
    batches = sorted({int(e["labels"]["batch"]) for e in matrix})
    print(f"build_matrix={json.dumps(matrix, sort_keys=True)}")
    print(f"batches={','.join(map(str, batches))}")


if __name__ == "__main__":
    main()
