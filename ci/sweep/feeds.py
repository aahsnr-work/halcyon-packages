"""Upstream version feeds for the sweeper — the port of andax's gh()/gh_tag()
/gh_commit()/get()/get_json()/find() helpers.

Only the stdlib (urllib) is used; every GitHub call carries GITHUB_TOKEN when
the environment provides one, exactly like the rhai helpers did.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request

GITHUB_API = "https://api.github.com"


class FeedError(Exception):
    """A feed could not produce a version (bad upstream data, no match)."""


def _gh_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "halcyon-packages-sweeper",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _headers_for(url: str) -> dict[str, str]:
    """GitHub auth only ever goes to api.github.com — the plain get()/get_json()
    feeds hit third-party hosts (SourceForge, AUR, opencode.net) and must not
    leak the token to them."""
    if url.startswith(GITHUB_API):
        return _gh_headers()
    return {"User-Agent": "halcyon-packages-sweeper"}


def _get(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers=_headers_for(url))


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(_get(url), timeout=60) as resp:
        return resp.read().decode()


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def fetch_headers(url: str) -> dict[str, str]:
    """GET and return only the response headers (the commits-count probe)."""
    with urllib.request.urlopen(_get(url), timeout=60) as resp:
        return dict(resp.headers.items())


def find_group(pattern: str, text: str, group: int = 1, dotall: bool = False) -> str:
    """andax find() port; a no-match is an error, not an empty string — a
    silent empty version would corrupt the spec."""
    m = re.search(pattern, text, re.DOTALL if dotall else 0)
    if not m:
        raise FeedError(f"no match for {pattern!r}")
    return m.group(group)


# ---- GitHub feeds ----------------------------------------------------------


def github_release_tag(repo: str) -> str:
    """gh() port: the tag of the repo's latest release (newest non-draft,
    non-prerelease), RAW — andax does not strip the leading `v` (verified:
    the sdbus-c++ sweep wrote v2.3.1). Callers that want an unprefixed
    version strip it themselves (rpm.version() does for Version lines)."""
    data = fetch_json(f"{GITHUB_API}/repos/{repo}/releases/latest")
    return data["tag_name"]


def _next_link(link: str) -> str:
    """The rel="next" target of a GitHub Link header, or empty."""
    for part in link.split(","):
        if 'rel="next"' in part:
            m = re.search(r"<([^>]+)>", part)
            if m:
                return m.group(1)
    return ""


def github_latest_tag(repo: str) -> str:
    """gh_tag() port: the newest git tag (releases or not), leading `v`
    stripped. Walks ALL pagination pages: zotero-class repos carry hundreds
    of tags and GitHub's /tags ordering is not newest-first, so a single
    page could miss the newest tag. The per-name v-strip before comparing
    is not cosmetic: Hyprland's tag set mixes `v0.56.2` with an ancient
    unprefixed `0.1.0-beta`, and rpmvercmp ranks a leading digit over a
    leading letter — comparing raw names picks the prehistoric tag.
    Empty when the repo has no tags — callers treat that as 'stay on the
    current version base'."""
    names: list[str] = []
    url: str | None = f"{GITHUB_API}/repos/{repo}/tags?per_page=100"
    for _ in range(20):  # 20 pages = 2000 tags; no halcyon upstream goes near it
        if not url:
            break
        req = urllib.request.Request(url, headers=_headers_for(url))
        with urllib.request.urlopen(req, timeout=60) as resp:
            names.extend(t["name"] for t in json.loads(resp.read().decode()))
            url = _next_link(resp.headers.get("Link", ""))
    if not names:
        return ""
    from vercmp import rpmvercmp

    best = ""
    for name in names:
        stripped = name.removeprefix("v")
        if not best or rpmvercmp(stripped, best) > 0:
            best = stripped
    return best


def github_newest_release_branch(repo: str, suffix: str = "-b") -> str:
    """The newest maintenance branch of a repo (hyprwm cuts a `vX.Y.Z-b`
    bugfix branch per release — that is the current stable line; there is no
    plain `stable` branch). Returns the full branch name (`v0.56.2-b`), empty
    when no branch matches the suffix."""
    names: list[str] = []
    url: str | None = f"{GITHUB_API}/repos/{repo}/branches?per_page=100"
    for _ in range(20):
        if not url:
            break
        req = urllib.request.Request(url, headers=_headers_for(url))
        with urllib.request.urlopen(req, timeout=60) as resp:
            names.extend(b["name"] for b in json.loads(resp.read().decode()))
            url = _next_link(resp.headers.get("Link", ""))
    candidates = [n for n in names if n.endswith(suffix)]
    if not candidates:
        return ""
    from vercmp import rpmvercmp

    best = candidates[0]
    for name in candidates[1:]:
        if rpmvercmp(name.removeprefix("v"), best.removeprefix("v")) > 0:
            best = name
    return best


def github_commit(repo: str, ref: str = "") -> str:
    """gh_commit() port: the tip commit of the default branch (or `ref`).
    Without a ref the commits endpoint returns a LIST — take its head."""
    data = fetch_json(
        f"{GITHUB_API}/repos/{repo}/commits/{ref}" if ref
        else f"{GITHUB_API}/repos/{repo}/commits"
    )
    return (data[0] if isinstance(data, list) else data)["sha"]


def github_commits_count(repo: str, commit: str) -> str:
    """Total commits up to `commit`, read off the Link header of a per_page=1
    listing (the rhai curl'd -I for this; urllib sees the same header)."""
    headers = fetch_headers(
        f"{GITHUB_API}/repos/{repo}/commits?per_page=1&sha={commit}"
    )
    link = headers.get("Link", "")
    m = re.search(r'page=([0-9]+)[^,]*rel="last"', link)
    return m.group(1) if m else ""


def github_contents_sha(repo: str, path: str, ref: str) -> str:
    """SHA of a path at `ref` (the hyprland submodule pins)."""
    from urllib.parse import quote

    data = fetch_json(
        f"{GITHUB_API}/repos/{repo}/contents/{quote(path)}?ref={ref}"
    )
    return data["sha"]


def format_commit_date(iso_date: str) -> str:
    """The hyprland spec's commit_date format: GNU date's
    `+%a %b %d %T %Y` on the author date. Shelling out to `date -d` keeps the
    output byte-identical to what the rhai produced (same binary, same TZ)."""
    proc = subprocess.run(
        ["date", "-d", iso_date, "+%a %b %d %T %Y"],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()
