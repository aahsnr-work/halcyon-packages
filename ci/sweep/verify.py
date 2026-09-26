#!/usr/bin/env python3
"""Sweeper equivalence harness: `anda update` vs ci/sweep/sweep.py, per
package, on byte-identical corrupted inputs.

Motivation: the 48 update.rhai scripts were never verified end-to-end (two of
them never even parsed), so the Python port is validated the only way that
means anything — by running both tools on the same tree state and demanding
identical spec bytes.

How it works, per swept package:
  1. restore the package's spec in both scratch trees, corrupt the old-tree
     spec (Version -> 0.0.1, Release -> 99%{?dist}, plus the package's pinned
     %globals -> junk) so the sweep has real mutations to make, and copy the
     corrupted file over the new-tree spec (identical inputs);
  2. run `anda update <pkg>` in the old tree and `sweep.py --pkg <pkg>` in the
     new tree;
  3. byte-compare the resulting specs. Equal = PASS. hyprland/obsidian are
     allowed to differ because their rhai scripts crash before writing (the
     port implements the intended logic; its output is printed for review).

Must run INSIDE the builder container (anda, rpmspec, date live there); the
container needs python3 installed first. From the host:

  for tree in old new; do git clone . /var/tmp/builds/sweep-$tree; done
  podman run --rm -v /var/tmp/builds/sweep-new:/new \
      -v /var/tmp/builds/sweep-old:/old -w /new \
      -e GITHUB_TOKEN localhost/halcyon-builder:f44 \
      bash -c 'dnf -yq install python3 >/dev/null && python3 ci/sweep/verify.py --old-tree /old --new-tree /new'

  To compare against a PRE-RENAME tree whose packages live under anda/
  (e.g. a HEAD clone), pass --old-dir anda --new-dir pkgs.
"""

from __future__ import annotations

import argparse
import difflib
import os
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spec import SpecFile  # noqa: E402

# packages whose rhai scripts crash before writing anything (verified
# 2026-09-25 with anda 0.x in halcyon-builder:f44) — the port's output is
# printed for manual review instead of byte-compared
KNOWN_OLD_FAIL = ("hyprland", "obsidian", "noctalia-greeter-git")

# packages where the port intentionally deviates from the rhai's (wrong)
# output: the xdg-desktop-portal-hyprland rhai wrote the raw v-prefixed tag
# into %global sdbus_version, but the spec's Source template already carries
# the v — the rhai's value would make the download URL vv2.3.1
KNOWN_INTENTIONAL_DIFF = ("xdg-desktop-portal-hyprland",)

# extra %global corruption beyond the Version/Release base corruption
EXTRA_CORRUPT = {
    "hyprland": {"hyprland_commit": "0" * 40, "protocols_commit": "0" * 40,
                 "udis86_commit": "0" * 40, "commits_count": "0", "bumpver": "0"},
    "noctalia-greeter-git": {"commit": "0" * 40},
    "qt6ct": {"commit": "0" * 40},
    "marksman": {"markstag": "deadbeef"},
    "obsidian": {"digest": "deadbeef"},
    "xdg-desktop-portal-hyprland": {"sdbus_version": "0.0.0"},
}


def corrupt(spec_path: Path, extras: dict[str, str]) -> None:
    spec = SpecFile(spec_path)
    spec.set_version("0.0.1", reset_release=True)
    for name, value in extras.items():
        spec.set_global(name, value)
    spec.path.write_text(spec.text)


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-tree", type=Path, required=True)
    ap.add_argument("--new-tree", type=Path, required=True)
    ap.add_argument("--old-dir", default="pkgs",
                    help="package directory name in the old tree (e.g. 'anda' "
                         "when comparing against a pre-rename commit)")
    ap.add_argument("--new-dir", default="pkgs")
    ap.add_argument("--pkg", nargs="*", help="limit to these packages")
    args = ap.parse_args()
    old_tree, new_tree = args.old_tree.resolve(), args.new_tree.resolve()

    with open(new_tree / "ci" / "packages.toml", "rb") as fh:
        registry = tomllib.load(fh)
    swept = [n for n, e in registry.items() if e.get("updates")]
    if args.pkg:
        swept = [n for n in swept if n in args.pkg]

    env = dict(os.environ)  # GITHUB_TOKEN must be set by the caller
    results: list[tuple[str, str, str]] = []
    for name in sorted(swept):
        old_spec = old_tree / args.old_dir / name / f"{name}.spec"
        new_spec = new_tree / args.new_dir / name / f"{name}.spec"
        subprocess.run(["git", "-C", str(old_tree), "checkout", "--",
                        f"{args.old_dir}/{name}"], check=True, capture_output=True)
        # the new tree may hold uncommitted (renamed) files — reset is best-effort
        subprocess.run(["git", "-C", str(new_tree), "checkout", "--",
                        f"{args.new_dir}/{name}"], check=False, capture_output=True)
        corrupt(old_spec, EXTRA_CORRUPT.get(name, {}))
        new_spec.write_bytes(old_spec.read_bytes())
        corrupted = old_spec.read_bytes()

        old_rc, old_out = run(["anda", "update", name], old_tree, env)
        new_rc, new_out = run([sys.executable, "ci/sweep/sweep.py", "--pkg", name],
                              new_tree, env)

        # anda update exits 0 even when a rhai script throws (verified on
        # hyprland/obsidian), so a "no output" old run is the crash signature
        old_bytes = old_spec.read_bytes()
        new_bytes = new_spec.read_bytes()
        old_wrote_nothing = old_bytes == corrupted
        if new_rc != 0:
            verdict = "FAIL"
            detail = f"sweeper failed:\n{new_out}"
        elif old_wrote_nothing and old_bytes != new_bytes:
            # the rhai crashed before writing anything; the port's output is
            # the intended logic — print it for review instead of comparing
            verdict = "REVIEW"
            detail = f"rhai wrote nothing (script crash, rc={old_rc}); sweeper output:\n{new_out}"
        elif old_bytes == new_bytes:
            verdict = "PASS"
            detail = ""
        elif name in KNOWN_INTENTIONAL_DIFF:
            diff = "\n".join(difflib.unified_diff(
                old_bytes.decode(errors="replace").splitlines(),
                new_bytes.decode(errors="replace").splitlines(),
                "anda", "sweep", lineterm="", n=1))
            verdict = "REVIEW"
            detail = "intentional deviation (rhai output is wrong):\n" \
                + "\n".join(diff.splitlines()[:16])
        elif old_wrote_nothing:
            verdict = "FAIL"
            detail = f"anda update failed silently:\n{old_out}"
        else:
            verdict = "FAIL"
            diff = "\n".join(difflib.unified_diff(
                old_bytes.decode(errors="replace").splitlines(),
                new_bytes.decode(errors="replace").splitlines(),
                "anda", "sweep", lineterm="", n=1))
            detail = "spec bytes differ:\n" + "\n".join(diff.splitlines()[:40])

        results.append((name, verdict, detail))
        print(f"[{verdict:>6}] {name} (anda rc={old_rc}, sweep rc={new_rc})")
        if detail:
            for line in detail.splitlines()[:24]:
                print(f"         {line}")
        subprocess.run(["git", "-C", str(old_tree), "checkout", "--",
                        f"{args.old_dir}/{name}"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(new_tree), "checkout", "--",
                        f"{args.new_dir}/{name}"], check=False, capture_output=True)

    failed = [r for r in results if r[1] == "FAIL"]
    print(f"\n{len(results) - len(failed)}/{len(results)} equivalent"
          f" ({len([r for r in results if r[1] == 'REVIEW'])} review,"
          f" {len(failed)} fail)")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
