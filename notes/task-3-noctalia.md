# Task 3 — noctalia (the shell) packaged, release-tracked

Requirement: "[NOTE: Latest stable branch must be used] noctalia".

## Upstream reality

noctalia-dev/noctalia has branches main / legacy-v4 / cachix / feat-freebsd —
no stable branch. "Latest stable" = the latest release tag: **v5.1.0**.

## Clarification from the maintainer

"Noctalia v5 is the current spec file and is not dependent on quickshell.
Check terra github repo for it." — confirmed: Terra's
`anda/desktops/noctalia/nightly/noctalia-nightly.spec` (frawhide) is the v5
C++/meson recipe (meson, gcc-c++, sdbus-cpp, wireplumber, … — no quickshell;
the `noctalia-qs`/`noctalia-legacy` variants are the quickshell v4 era).

## Change

- `pkgs/noctalia/noctalia.spec` — Terra's nightly recipe adapted to the
  release tarball: Version 5.1.0, Source0 = tag archive,
  `%autosetup -n noctalia-%{version}`, meson build, third_party license
  collection, desktop-file-validate. The nightly's commit-hash sed now
  inserts `v%{version}` instead of a commit hash.
- Registry: `[noctalia] batch = 0` + sweep feed `github-release`
  (noctalia-dev/noctalia). Batch 0 = all build deps are Fedora 44; the
  greeter (batch 1) builds after the shell by design again.
- Never built anywhere — its first Copr build is the validation.
