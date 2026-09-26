# Task 10 — secret + commit + push + the first cascade

The TODO's cutover block, with one deviation recorded below.

## Checklist state at execution

- `COPR_CLICONF` secret: already set (2026-09-25, verified via
  `gh secret list`) — the `< ~/.config/copr` step is a no-op unless the
  token rotates (180-day expiry; a wave of 401s means regenerate + re-set).
- Commit: the whole migration tree (pkgs/ rename, ci/sweep, new workflows,
  repo/halcyon.repo, docs, notes/) as one commit with the TODO's message:
  `migrate builds to Fedora Copr; replace the anda sweep with ci/sweep`.
- `.zcode/` + `.zcodeignore` (session artifacts) added to .gitignore so
  the commit carries only project files.

## Deviation: no separate `gh workflow run copr-build.yml`

The TODO's final line dispatches the cascade manually. Skipped, on
purpose: the push itself triggers `copr-build.yml` (path filter covers
`pkgs/**`, `ci/**`, `.github/builder/**` — all touched), and the
workflow's concurrency group (`cancel-in-progress: false`) would just
queue the dispatched duplicate behind the push run, re-building the same
matrix. One push, one cascade.

## What to watch

- The Actions run: validate → manifest → submit1..5/wait1..5 (batch 4 =
  texlive-texmf + onlyoffice — the heavy wave, ~2 h, first real build of
  the staged brp-hook fixes).
- `copr-cli monitor halcyon` — green per package as each wave lands.
- The cascade also closes the two open validation items: xwiimote-ng
  (never built) and noctalia (new, task 3).
- After green: consume test — `dnf copr enable aahsnr-work/halcyon
  fedora-44` in a fresh Fedora 44 container and install a few packages.

## Status

<!-- filled in at execution -->
