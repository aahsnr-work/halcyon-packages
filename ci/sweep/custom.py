"""The custom version feeds — 1:1 Python ports of the 11 update.rhai scripts
that carry real logic (the other 35 are one-liner gh()/gh_tag() sweeps driven
from ci/packages.toml).

Two intentional deviations from the rhai, both bug fixes (the rhai versions
never ran successfully — see TODO.md's sweep-verification note):

- hyprland: the rhai referenced an undefined `old_tag` (it would abort) and
  rewrote the commit date with a whole-spec string substitution (which
  corrupted the spec's %global commit_date line by colliding with changelog
  text). The port compares against the spec's version base and rewrites the
  %global line in place.
- obsidian: the rhai used `#` lines as comments — a rhai syntax error, so the
  script never parsed. The port implements the documented intent.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import feeds
from spec import SpecFile


def _parse_int(value: str | None) -> int:
    try:
        return int(value or "")
    except ValueError:
        return 0


def custom_bitwarden(spec: SpecFile, pkg_dir: Path) -> None:
    # bitwarden/clients cuts other tags too; the raw-text scan picks the first
    # desktop-v tag of the releases list (GitHub orders newest-first).
    text = feeds.fetch_text(
        "https://api.github.com/repos/bitwarden/clients/releases?per_page=30"
    )
    tag = feeds.find_group(r'"tag_name":"desktop-v([^"]+)"', text)
    spec.set_version(tag)


def custom_bun(spec: SpecFile, pkg_dir: Path) -> None:
    # bun publishes no GitHub release feed; the LATEST file is the official
    # channel. Version tracks the -baseline build of the release zip.
    spec.set_version(feeds.fetch_text(
        "https://raw.githubusercontent.com/oven-sh/bun/main/LATEST").strip())


def custom_gnuplot(spec: SpecFile, pkg_dir: Path) -> None:
    # gnuplot publishes on SourceForge, not GitHub; the linux filename of
    # best_release.json carries the version.
    data = feeds.fetch_json("https://sourceforge.net/projects/gnuplot/best_release.json")
    filename = data["platform_releases"]["linux"]["filename"]
    spec.set_version(feeds.find_group(r"gnuplot-([0-9.]+)\.tar\.gz$", filename))


def custom_hyprland(spec: SpecFile, pkg_dir: Path) -> None:
    # hyprland tracks the newest upstream RELEASE only (maintainer: no git
    # snapshots). Version is the plain release tag; the official
    # source-vX.Y.Z.tar.gz asset bundles every subproject, so there is
    # nothing else to pin — a new release is just a version bump.
    repo = "hyprwm/Hyprland"
    tag = feeds.github_release_tag(repo)
    if not tag:
        raise feeds.FeedError("hyprland: no release found upstream")
    spec.set_version(tag.removeprefix("v"))


def custom_marksman(spec: SpecFile, pkg_dir: Path) -> None:
    # the raw date tag goes into %markstag for the source URLs; the version is
    # the tag with dashes converted to dots (RPM versions cannot carry dashes)
    tag = feeds.github_release_tag("artempyanykh/marksman")
    spec.set_global("markstag", tag)
    spec.set_version(tag.replace("-", "."))


def custom_noctalia_greeter_git(spec: SpecFile, pkg_dir: Path) -> None:
    # tracks the noctalia-dev/noctalia-greeter branch tip, not a release: the
    # spec pins the commit in a %global and keeps the last tag as the version
    # base with a ^N snapshot counter — a new commit under the same tag bumps
    # the counter, a new tag resets it. The Release: line is left alone.
    repo = "noctalia-dev/noctalia-greeter"
    old_commit = feeds.find_group(
        r"(?m)^%global[ \t]+commit[ \t]+(\S+)", spec.text)
    new_commit = feeds.github_commit(repo)
    # old_version as rpmdev sees it (the Version line carries %{shortcommit})
    proc = subprocess.run(
        ["rpmspec", "-q", "--qf", "%{version}", str(pkg_dir / spec.path.name)],
        check=True, capture_output=True, text=True, cwd=pkg_dir,
    )
    old_version = proc.stdout.strip()
    old_base = re.sub(r"\^.*", "", old_version)
    # the version base is unprefixed (github_latest_tag strips the v; the
    # Sources carry commit SHAs so no URL is affected)
    tag_raw = feeds.github_latest_tag(repo)
    new_tag = old_base if not tag_raw else tag_raw.replace("-", "~")

    from vercmp import vercmp_rc

    ec = vercmp_rc(old_version, new_tag)
    if old_commit != new_commit or ec == 12:
        if ec == 12:
            # newer tag: reset the snapshot counter
            spec.set_snapshot_version(new_tag, None)
        else:
            # same version base: bump the snapshot counter
            m = re.search(r"(?m)^Version:[ \t]*[^ \t]*\^(\d+)", spec.text)
            counter = int(m.group(1)) + 1 if m else 1
            spec.set_snapshot_version(old_base, counter)
        spec.set_global("commit", new_commit)


def custom_obsidian(spec: SpecFile, pkg_dir: Path) -> None:
    # the newest obsidianmd/obsidian-releases release that ships the desktop
    # linux tarball; the release's sha256 asset digest is pinned in %global
    # digest for the %prep checksum ('none' skips the check when upstream
    # publishes no digest)
    text = feeds.fetch_text(
        "https://api.github.com/repos/obsidianmd/obsidian-releases/releases?per_page=30"
    )
    spec.set_version(feeds.find_group(r'"name":"obsidian-([0-9.]+)\.tar\.gz"', text))
    try:
        digest = feeds.find_group(
            r'"name":"obsidian-[0-9.]+\.tar\.gz".*?"digest":"sha256:([0-9a-f]{64})"',
            text, dotall=True,
        )
    except feeds.FeedError:
        digest = "none"
    spec.set_global("digest", digest)


def custom_opencode(spec: SpecFile, pkg_dir: Path) -> None:
    # the v2 line ships through opencode.ai's own update API, not GitHub
    # releases; the npm scope carrying the cli-linux-x64 tarball is resolved
    # from the same endpoint and Source0 is rewritten when the scope moves.
    meta = feeds.fetch_text("https://opencode.ai/update/api/latest/cli/npm")
    spec.set_version(feeds.find_group(r'"version":"([^"]+)"', meta))
    scope = "@opencode"
    m = re.search(r'"package":"([^"]*)/cli"', meta)
    if m:
        scope = m.group(1)
    if scope != "@opencode":
        spec.set_source(
            0,
            "https://registry.npmjs.org/" + scope
            + "%2Fcli-linux-x64/-/cli-linux-x64-%{version}.tgz",
        )


def custom_qt6ct(spec: SpecFile, pkg_dir: Path) -> None:
    # GitLab releases of opencode.net/trialuser/qt6ct (the canonical repo; the
    # GitHub mirror lags behind). The spec pins the release commit: the
    # Source0 archive URL follows the %global commit.
    releases = feeds.fetch_json(
        "https://www.opencode.net/api/v4/projects/5459/releases?per_page=1")
    release = releases[0]
    spec.set_version(release["tag_name"])
    spec.set_global("commit", release["commit"]["id"])


def custom_ticktick(spec: SpecFile, pkg_dir: Path) -> None:
    # TickTick publishes no first-party version feed, but the AUR package
    # tracks it: the AUR maintainer bumps pkgver on every upstream release.
    # Version is pkgver-pkgrel — keep pkgver only.
    data = feeds.fetch_json("https://aur.archlinux.org/rpc/v5/info?arg%5B%5D=ticktick")
    results = data.get("results") or []
    aur_version = results[0]["Version"] if results else ""
    if not aur_version:
        raise feeds.FeedError("ticktick: the AUR RPC returned no version")
    spec.set_version(re.sub(r"-[^-]*$", "", aur_version))


def custom_xdg_desktop_portal_hyprland(spec: SpecFile, pkg_dir: Path) -> None:
    # the portal release plus the sdbus-c++ release the bundled Source1
    # tarball is pinned to. The global stays unprefixed — the Source template
    # carries the v itself (the rhai wrote the raw v-tag and would have made
    # the URL vv2.3.1; it never ran to catch it).
    spec.set_version(feeds.github_release_tag("hyprwm/xdg-desktop-portal-hyprland"))
    spec.set_global(
        "sdbus_version",
        feeds.github_release_tag("Kistler-Group/sdbus-cpp").removeprefix("v"),
    )
