# Task 2 — hyprland tracks the latest stable line

Requirement: "[NOTE: Latest stable branch must be used] hyprland".

## Upstream reality (checked via the GitHub API, 2026-09-26)

hyprwm/Hyprland keeps NO `stable` branch. What it does keep: a bugfix branch
`vX.Y.Z-b` per release (`v0.56.2-b` is the newest today, holding backported
fixes between releases). "Latest stable branch" therefore = the newest
`vX.Y.Z-b` branch tip.

## Change

- `ci/sweep/feeds.py`: new `github_newest_release_branch(repo, suffix="-b")`
  helper (paginated /branches, newest by rpmvercmp on the v-stripped name).
- `ci/sweep/custom.py custom_hyprland`: the tracker now resolves the newest
  `-b` branch, and pins its tip:
  - `new_commit = github_commit(repo, ref=branch)`
  - commit count + author date + submodule SHAs all resolve at that branch
  - version base = branch name minus `v`/`-b` (0.56.2 today)
  - bumpver counter semantics unchanged: revision change → +1; a newer
    stable line (v0.56.3-b appearing) resets the counter via the existing
    vercmp 12 path.
- The spec itself needed no change: Source0 archives the pinned commit, and
  the submodule Sources pin their SHAs at the same ref.

## Verification

- Live sweep dry-run: hyprland resolved 0.56.2 from `v0.56.2-b` and detected
  the branch tip movement without writing (dry-run).

## ADDENDUM 2026-09-26 — superseded: release-only tracking (maintainer)

The maintainer wants the build version to show only RELEASES (no
`^N.git<sha>` snapshots). The spec dropped the whole git-snapshot
machinery (bumpver/commit/commits_count/commit_date globals, the commit-
archive Source0 branch, the submodule Source2/3 + their %prep unpack and
GIT_* seds) — the official `source-vX.Y.Z.tar.gz` release asset bundles
every subproject (verified: 149 subproject files in the v0.56.2 tarball),
so the release form needs no submodule pins at all. `custom_hyprland` is
now a pure release tracker: `github_release_tag()` → `set_version()` —
a new upstream release is just a version bump (Release resets to 1 per
the anda semantics). Live check: sweep reports `unchanged: hyprland
(0.56.2)` — the newest release is already the packaged version.

Note: the ci/sweep equivalence harness cannot be rerun for this change —
it compares against `anda update`, which no longer exists after the Copr
migration. The divergence from the rhai semantics here is deliberate
(release-only vs git-snapshot).
