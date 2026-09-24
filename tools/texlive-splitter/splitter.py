#!/usr/bin/env python3
"""TeX Live snapshot -> Arch-style grouped RPM splitter.

Converts a dated tlnet-archive snapshot into one `texlive-texmf` source package
whose subpackages mirror Arch's grouping (texlive-basic, texlive-binextra,
texlive-latexextra, texlive-fontsextra, texlive-lang*, ... + texlive-meta).

Reference implementation for the parsing logic: Arch's texlive-texmf PKGBUILD
(gitlab.archlinux.org/archlinux/packaging/packages/texlive-texmf).

Usage:
  ./splitter.py --snapshot 20260901 [--archive-root https://texlive.info/tlnet-archive] [--out ./generated]

Steps:
  1. fetch install-tl-unx.tar.gz from <archive-root>/<snapshot>/tlnet
  2. install to a staging dir via install-tl --profile (scheme-medium, no docs
     in the base set; docs land in texlive-doc)
  3. parse <staging>/tlpkg/texlive.tlpdb -> per-collection runfiles/deps/fragments
  4. generate texlive-texmf.spec (subpackage per group) + file lists
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# collection name -> RPM subpackage suffix (Arch naming)
GROUP_MAP = {
    "basic": "basic",
    "bibtexextra": "bibtexextra",
    "binextra": "binextra",
    "context": "context",
    "fontsextra": "fontsextra",
    "fontsrecommended": "fontsrecommended",
    "fontutils": "fontutils",
    "formatsextra": "formatsextra",
    "games": "games",
    "humanities": "humanities",
    "latex": "latex",
    "latexextra": "latexextra",
    "latexrecommended": "latexrecommended",
    "luatex": "luatex",
    "mathscience": "mathscience",
    "metapost": "metapost",
    "music": "music",
    "pictures": "pictures",
    "plaingeneric": "plaingeneric",
    "pstricks": "pstricks",
    "publishers": "publishers",
    "xetex": "xetex",
    # lang collections keep the lang- prefix: collection-langchinese -> texlive-langchinese
}


def collection_to_group(collection: str) -> str | None:
    """collection-<name> -> texlive-<group>, or None for non-groups (texworks, wintypes)."""
    if not collection.startswith("collection-"):
        return None
    name = collection.removeprefix("collection-")
    if name in ("texworks", "wintools"):
        return None
    # lang collections keep their name: collection-langchinese -> texlive-langchinese
    group = GROUP_MAP.get(name, name)
    return f"texlive-{group}"


def fetch_installer(snapshot: str, archive_root: str, workdir: Path) -> Path:
    url = f"{archive_root}/{snapshot}/tlnet/install-tl-unx.tar.gz"
    tarball = workdir / "install-tl-unx.tar.gz"
    subprocess.run(
        [
            "curl",
            "-fsSL",
            "--retry",
            "5",
            "--retry-all-errors",
            url,
            "-o",
            str(tarball),
        ],
        check=True,
    )
    subprocess.run(["gzip", "-t", str(tarball)], check=True)
    subprocess.run(["tar", "-xzf", str(tarball), "-C", str(workdir)], check=True)
    installers = list(workdir.glob("install-tl-*/install-tl"))
    if not installers:
        sys.exit("FATAL: install-tl not found in the downloaded archive")
    return installers[0]


def install_snapshot(
    installer: Path, snapshot: str, archive_root: str, staging: Path
) -> None:
    profile = workdir_profile(snapshot, archive_root, staging)
    subprocess.run(
        [str(installer), "--profile", str(profile)],
        check=True,
        env={
            "PATH": "/usr/bin:/bin",
            "TEXLIVE_INSTALL_ENV_NOCREATE": "1",
            "TEXLIVE_INSTALL_PREFIX": str(staging),
        },
    )


def workdir_profile(snapshot: str, archive_root: str, staging: Path) -> Path:
    p = staging / "texlive.profile"
    p.write_text(
        "\n".join(
            [
                "selected_scheme scheme-medium",
                f"TEXDIR {staging}",
                f"TEXMFCONFIG {staging}/texmf-config",
                f"TEXMFVAR {staging}/texmf-var",
                f"TEXMFLOCAL {staging}/texmf-local",
                f"TEXMFSYSCONFIG {staging}/texmf-config",
                f"TEXMFSYSVAR {staging}/texmf-var",
                f"repository {archive_root}/{snapshot}/tlnet",
                "option_doc 1",
                "option_src 0",
                "instopt_adjustpath 0",
                "instopt_adjustrepo 0",
                "instopt_letter 0",
                "instopt_portable 1",
                "instopt_write18_restricted 1",
                "tlpdbopt_autobackup 0",
                "tlpdbopt_install_docfiles 1",
                "tlpdbopt_install_srcfiles 0",
                "",
            ]
        )
    )
    return p


def parse_tlpdb(tlpdb_path: Path) -> dict[str, dict]:
    """Parse texlive.tlpdb into {pkgname: {runfiles, depend, execute, shortdesc}}.

    tlpdb layout: a block starts with `name <pkg>`; its fields are top-level
    lines (`runfiles size=N`, `depend x`, ...), and the runfiles file list is
    the run of space-prefixed continuation lines that follows the `runfiles`
    line until the next top-level line.
    """
    packages: dict[str, dict] = {}
    current: dict | None = None
    for raw in tlpdb_path.read_text(errors="replace").splitlines():
        if not raw.strip():
            current = None
            continue
        if raw.startswith(" "):  # continuation line
            if current is None or not current.get("runfiles_cont"):
                continue
            current["runfiles"].append(raw.strip())
            continue
        if current is not None:
            current["runfiles_cont"] = False
        if raw.startswith("name "):
            name = raw.removeprefix("name ").strip()
            current = packages.setdefault(
                name, {"runfiles": [], "depend": [], "execute": []}
            )
            current["runfiles_cont"] = False
            continue
        if current is None:
            continue
        if raw.startswith("runfiles"):
            current["runfiles_cont"] = True
        elif raw.startswith(("shortdesc ",)):
            current["shortdesc"] = raw.removeprefix("shortdesc ").strip()
        elif raw.startswith("depend "):
            current["depend"].append(raw.removeprefix("depend ").strip())
        elif raw.startswith("execute "):
            current["execute"].append(raw.removeprefix("execute ").strip())
    return packages


def generate_spec(snapshot: str, staging: Path, outdir: Path) -> Path:
    tlpdb = staging / "tlpkg" / "texlive.tlpdb"
    packages = parse_tlpdb(tlpdb)
    groups: dict[str, dict] = {"texlive-doc": {"runfiles": [], "depend": [], "execute": []}}
    for pkgname, data in packages.items():
        if not pkgname.startswith("collection-"):
            continue
        group = collection_to_group(pkgname)
        if group is None:
            continue
        groups.setdefault(group, {"runfiles": [], "depend": [], "execute": []})
        for dep in data["depend"]:
            if dep.startswith("collection-"):
                dep_group = collection_to_group(dep)
                if dep_group and dep_group != group:
                    groups[group]["depend"].append(dep_group)
        for rf in data["runfiles"]:
            if rf.startswith("texmf-dist/doc/"):
                groups["texlive-doc"]["runfiles"].append(rf)
            else:
                groups[group]["runfiles"].append(rf)
        groups[group]["execute"].extend(data["execute"])

    subpackages = sorted(groups)
    lines = [
        "# GENERATED by splitter.py from tlnet-archive snapshot "
        + snapshot
        + " — do not edit by hand",
        f"# snapshot: {snapshot}",
        "# NOTE: the %files lists reference the local install staging tree "
        "(%_tl_staging); before building this as an SRPM the staging tree must "
        "be repackaged into sources the build chroot can see.",
        "Name: texlive-texmf",
        f"Version: {snapshot}",
        "Release: 1",
        "License: GPL+ and others (TeX Live collective licenses)",
        "BuildArch: noarch",
        "",
        "%global _tl_staging " + str(staging),
        "%global _tl_texmf " + str(staging / "texmf-dist"),
        "",
        "%description",
        "TeX Live snapshot packages (splitter-generated, Arch-style grouping).",
        "",
    ]
    for group in subpackages:
        files = groups[group]["runfiles"]
        deps = sorted(set(groups[group]["depend"]))
        # -n declares each subpackage by its own full name (group already
        # carries the "texlive-" prefix from collection_to_group) instead of
        # letting rpm treat `group` as a suffix of Name, which would produce
        # texlive-texmf-texlive-basic instead of texlive-basic.
        lines.append(f"%package -n {group}")
        lines.append(
            f"Summary: TeX Live {group.removeprefix('texlive-')} collection (snapshot {snapshot})"
        )
        for dep in deps:
            # dep is already a fully-qualified subpackage name
            # (e.g. "texlive-langchinese"), not a suffix of %{name}.
            lines.append(f"Requires: {dep}")
        lines.append("")
        lines.append(f"%description -n {group}")
        lines.append(f"TeX Live {group} collection files from snapshot {snapshot}.")
        lines.append("")
        lines.append(f"%files -n {group}")
        # NOTE: no %license here — the snapshot does not ship per-group
        # LICENSE.<group> files; add license handling once the file layout of
        # the generated install tree has been checked.
        for rf in files:
            lines.append(f"%{{_tl_texmf}}/{rf.removeprefix('texmf-dist/')}")
        for frag in groups[group]["execute"]:
            if "AddFormat" in frag or "addMap" in frag or "AddHyphen" in frag:
                lines.append("%dir %{_tl_staging}/tlpkg/halcyon-fragments")
                lines.append(
                    "%{_tl_staging}/tlpkg/halcyon-fragments/" + group + ".fragments"
                )
                break
        lines.append("")

    outdir.mkdir(parents=True, exist_ok=True)
    spec = outdir / "texlive-texmf.spec"
    spec.write_text("\n".join(lines) + "\n")
    return spec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True, help="tlnet-archive date, YYYYMMDD")
    ap.add_argument("--archive-root", default="https://texlive.info/tlnet-archive")
    ap.add_argument("--out", default="./generated")
    args = ap.parse_args()

    workdir = Path(f"/var/tmp/tl-splitter-{args.snapshot}")
    staging = workdir / "staging"
    staging.mkdir(parents=True, exist_ok=True)

    installer = fetch_installer(args.snapshot, args.archive_root, workdir)
    install_snapshot(installer, args.snapshot, args.archive_root, staging)
    spec = generate_spec(args.snapshot, staging, Path(args.out))
    print(f"OK: generated {spec}")
    print("next: build the whole set atomically in mock (one snapshot for all groups),")
    print("then publish to repo/fedora/44/x86_64 and bump texlive-meta consumers.")


if __name__ == "__main__":
    main()
