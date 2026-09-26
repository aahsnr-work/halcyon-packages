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
