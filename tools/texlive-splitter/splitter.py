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


def snapshot_url(snapshot: str, archive_root: str) -> str:
    """tlnet-archive URL root for a snapshot date (YYYYMMDD).

    The archive is laid out as YYYY/MM/DD (20260901 -> 2026/09/01)."""
    if len(snapshot) != 8 or not snapshot.isdigit():
        sys.exit(f"FATAL: --snapshot must be YYYYMMDD, got {snapshot!r}")
    return f"{archive_root}/{snapshot[:4]}/{snapshot[4:6]}/{snapshot[6:]}"


def fetch_installer(snapshot: str, archive_root: str, workdir: Path) -> Path:
    url = f"{snapshot_url(snapshot, archive_root)}/tlnet/install-tl-unx.tar.gz"
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
    installer: Path, snapshot: str, archive_root: str, staging: Path, scheme: str
) -> None:
    profile = workdir_profile(snapshot, archive_root, staging, scheme)
    subprocess.run(
        [
            str(installer),
            "--profile",
            str(profile),
            "--repository",
            f"{snapshot_url(snapshot, archive_root)}/tlnet",
        ],
        check=True,
        env={
            "PATH": "/usr/bin:/bin",
            "TEXLIVE_INSTALL_ENV_NOCREATE": "1",
            "TEXLIVE_INSTALL_PREFIX": str(staging),
        },
    )


def workdir_profile(
    snapshot: str, archive_root: str, staging: Path, scheme: str
) -> Path:
    p = staging / "texlive.profile"
    # repository is passed on the CLI (--repository) — modern install-tl
    # profiles reject a `repository` key
    p.write_text(
        "\n".join(
            [
                f"selected_scheme {scheme}",
                f"TEXDIR {staging}",
                f"TEXMFCONFIG {staging}/texmf-config",
                f"TEXMFVAR {staging}/texmf-var",
                f"TEXMFLOCAL {staging}/texmf-local",
                f"TEXMFSYSCONFIG {staging}/texmf-config",
                f"TEXMFSYSVAR {staging}/texmf-var",
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
            if current is None:
                continue
            entry = raw.strip()
            # annotation suffix: details="Package documentation"
            if " details=" in entry:
                entry = entry.split(" details=", 1)[0].strip()
            if current.get("runfiles_cont"):
                current["runfiles"].append(entry)
            elif current.get("docfiles_cont"):
                current["docfiles"].append(entry)
            continue
        if current is not None:
            current["runfiles_cont"] = False
            current["docfiles_cont"] = False
        if raw.startswith("name "):
            name = raw.removeprefix("name ").strip()
            current = packages.setdefault(
                name,
                {"runfiles": [], "docfiles": [], "depend": [], "execute": []},
            )
            continue
        if current is None:
            continue
        if raw.startswith("runfiles"):
            current["runfiles_cont"] = True
        elif raw.startswith("docfiles"):
            current["docfiles_cont"] = True
        elif raw.startswith(("shortdesc ",)):
            current["shortdesc"] = raw.removeprefix("shortdesc ").strip()
        elif raw.startswith("depend "):
            current["depend"].append(raw.removeprefix("depend ").strip())
        elif raw.startswith("execute "):
            current["execute"].append(raw.removeprefix("execute ").strip())
    return packages


def resolve_scheme_collections(tlpdb: dict[str, dict], scheme: str) -> set[str]:
    """All collection-* packages a scheme pulls in, transitively."""
    if scheme not in tlpdb:
        sys.exit(f"FATAL: scheme {scheme!r} not found in the tlpdb")
    collections: set[str] = set()
    stack = [_dep_name(d) for d in tlpdb[scheme]["depend"]]
    while stack:
        dep = stack.pop()
        if dep.startswith("collection-") and dep not in collections:
            collections.add(dep)
            stack.extend(
                _dep_name(d) for d in tlpdb.get(dep, {"depend": []})["depend"]
            )
    return collections


def _dep_name(dep: str, platform: str = "x86_64-linux") -> str:
    """Resolve a tlpdb depend token to the package name for our platform.

    Plain deps may be platform-qualified (synctex.x86_64-linux) or carry the
    ARCH placeholder install-tl substitutes (biber.ARCH)."""
    name = dep.split(":", 1)[0]
    if name.endswith(".ARCH"):
        name = name[: -len(".ARCH")] + "." + platform
    return name


def _scheme_collection_order(
    scheme_data: dict, packages: dict[str, dict], installed: set[str]
) -> list[str]:
    """The scheme's collections in depend order (scheme deps first, then any
    transitive ones)."""
    order: list[str] = []
    stack = [_dep_name(d) for d in scheme_data["depend"]]
    while stack:
        dep = stack.pop()
        if dep in order or dep not in installed:
            continue
        if dep.startswith("collection-"):
            order.append(dep)
        stack.extend(
            _dep_name(d) for d in packages.get(dep, {"depend": []})["depend"]
        )
    return order



def _claim(groups, target, rf, files_seen):
    if rf in files_seen:
        return
    files_seen.add(rf)
    groups[target]["runfiles"].append(rf)

def generate_spec(
    snapshot: str, staging: Path, outdir: Path, scheme: str = "scheme-medium",
    docs: bool = True,
) -> Path:
    tlpdb = staging / "tlpkg" / "texlive.tlpdb"
    packages = parse_tlpdb(tlpdb)
    installed = resolve_scheme_collections(packages, scheme)
    # process collections in the scheme's depend order so shared member
    # packages are owned deterministically by the first claiming collection
    scheme_data = packages[scheme]
    ordered = [
        c
        for c in _scheme_collection_order(scheme_data, packages, installed)
        if c in installed
    ]

    groups: dict[str, dict] = {}
    if docs:
        groups["texlive-doc"] = {"runfiles": [], "depend": [], "execute": []}
    claimed: set[str] = set()
    # a shared file (fonts READMEs, doc/info) may be reached through several
    # member packages — rpm rejects duplicate %files entries, so the first
    # attribution wins everywhere
    files_seen: set[str] = set()
    for pkgname in ordered:
        data = packages[pkgname]
        group = collection_to_group(pkgname)
        if group is None:
            continue
        groups.setdefault(group, {"runfiles": [], "depend": [], "execute": []})
        for dep in data["depend"]:
            dep = _dep_name(dep)
            if dep.startswith("collection-"):
                dep_group = collection_to_group(dep)
                if dep_group and dep_group != group:
                    groups[group]["depend"].append(dep_group)
        # transitive member closure: collections pull packages whose own
        # depend lists pull more packages — every reached package's files
        # belong to this collection's group (first claiming collection wins)
        stack = [_dep_name(d) for d in data["depend"]]
        seen: set[str] = set()
        while stack:
            dep = stack.pop()
            if dep in seen or dep.startswith("collection-"):
                continue
            member = packages.get(dep)
            if member is None:
                continue
            seen.add(dep)
            stack.extend(_dep_name(d) for d in member["depend"])
            # docfiles are the package's documentation — always texlive-doc
            # (skipped entirely in --no-docs builds)
            for rf in member["docfiles"]:
                if not docs:
                    continue
                if rf.startswith("RELOC/"):
                    rf = "texmf-dist/" + rf[len("RELOC/"):]
                if rf.startswith("texmf-dist/"):
                    _claim(groups, "texlive-doc", rf, files_seen)
            for rf in member["runfiles"]:
                # RELOC/ marks files whose real root is the texmf tree
                if rf.startswith("RELOC/"):
                    rf = "texmf-dist/" + rf[len("RELOC/"):]
                # this set is noarch (BuildArch: noarch); the bin/ tree
                # (texlive-bin sources) is a follow-up split of its own
                if not rf.startswith("texmf-dist/"):
                    continue
                if rf.startswith("texmf-dist/doc/"):
                    if not docs:
                        continue
                    _claim(groups, "texlive-doc", rf, files_seen)
                else:
                    _claim(groups, group, rf, files_seen)
            groups[group]["execute"].extend(member["execute"])
        claimed.update(seen)

    # scheme-level plain deps no collection claims (e.g. scheme-small's
    # babel-* set): their files go to texlive-basic, the root group
    for dep in scheme_data["depend"]:
        dep = _dep_name(dep)
        if dep.startswith("collection-") or dep in claimed or dep not in packages:
            continue
        claimed.add(dep)
        member = packages[dep]
        groups.setdefault("texlive-basic", {"runfiles": [], "depend": [], "execute": []})
        for rf in member["docfiles"]:
            if not docs:
                continue
            if rf.startswith("RELOC/"):
                rf = "texmf-dist/" + rf[len("RELOC/"):]
            if rf.startswith("texmf-dist/"):
                _claim(groups, "texlive-doc", rf, files_seen)
        for rf in member["runfiles"]:
            if rf.startswith("RELOC/"):
                rf = "texmf-dist/" + rf[len("RELOC/"):]
            if not rf.startswith("texmf-dist/"):
                continue
            if rf.startswith("texmf-dist/doc/"):
                if not docs:
                    continue
                _claim(groups, "texlive-doc", rf, files_seen)
            else:
                _claim(groups, "texlive-basic", rf, files_seen)
        groups["texlive-basic"]["execute"].extend(member["execute"])
        claimed.add(dep)

    # install-tl regenerates this manifest at the texmf root
    groups["texlive-basic"]["runfiles"].append("texmf-dist/ls-R")

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
        # NOTE: the AddFormat/addMap/AddHyphen execute fragments are not
        # packaged yet — wiring them up needs the fedora texlive post-install
        # macros (formats/maps/hyphenation regeneration); follow-up work.
        lines.append("")

    outdir.mkdir(parents=True, exist_ok=True)
    spec = outdir / "texlive-texmf.spec"
    spec.write_text("\n".join(lines) + "\n")
    return spec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True, help="tlnet-archive date, YYYYMMDD")
    ap.add_argument(
        "--scheme",
        default="scheme-medium",
        help="TeX Live scheme to generate (scheme-basic/small/medium/full/...)",
    )
    ap.add_argument("--archive-root", default="https://texlive.info/tlnet-archive")
    ap.add_argument("--out", default="./generated")
    ap.add_argument(
        "--tlpdb-only",
        action="store_true",
        help="fetch only the snapshot tlpdb — the %%files lists derive from it "
        "alone; skip the local staging install (the build chroot stages its "
        "own tree from the archive URL at build time)",
    )
    ap.add_argument(
        "--no-docs",
        action="store_true",
        help="package no docfiles (option_doc 0) — ~70 percent of the bulk",
    )
    args = ap.parse_args()

    workdir = Path(f"/var/tmp/tl-splitter-{args.snapshot}")
    staging = workdir / "staging"
    staging.mkdir(parents=True, exist_ok=True)

    if not args.tlpdb_only:
        installer = fetch_installer(args.snapshot, args.archive_root, workdir)
        install_snapshot(installer, args.snapshot, args.archive_root, staging, args.scheme)
    else:
        tlpdb_dest = workdir / "texlive.tlpdb"
        tlpdb_dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "curl", "-fsSL", "--retry", "5", "--retry-all-errors",
                f"{snapshot_url(args.snapshot, args.archive_root)}/tlnet/"
                "tlpkg/texlive.tlpdb",
                "-o", str(tlpdb_dest),
            ],
            check=True,
        )
        tlpkg = staging / "tlpkg"
        tlpkg.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy(tlpdb_dest, tlpkg / "texlive.tlpdb")
    spec = generate_spec(args.snapshot, staging, Path(args.out), args.scheme, docs=not args.no_docs)
    print(f"OK: generated {spec}")
    print("next: adapt-spec.py writes the buildable anda package spec,")
    print("then publish to the R2 bucket (one snapshot for all groups).")


if __name__ == "__main__":
    main()
