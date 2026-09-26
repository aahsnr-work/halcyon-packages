# notes/texlive-rolling-plan — the Arch-shaped rolling TeX Live redesign

2026-09-26. Requirement: the whole texlive-full scheme **without
documentation** in the Copr repo, as **subgroups like Arch Linux's texlive
packages**, on a **rolling release model** — every 2 weeks on Wednesday
(maintainer's choices after the per-group vs one-spec question).

## What was built

- **40 per-group specs** replace the one-spec `texlive-texmf` monolith:
  `pkgs/texlive-<group>/texlive-<group>.spec` for the 39 collection groups
  + `pkgs/texlive-meta/texlive-meta.spec`. Group names identical to Arch
  Linux's (texlive-basic … texlive-xetex, the lang* set) — existing
  installs upgrade in place. Registry: batch 5 entries, no updates tables
  (the Monday sweep never touches them).
- **The roll driver** `tools/texlive-splitter/roll.py` (stdlib only):
  1. probe the newest daily snapshot:
     HEAD `<archive-root>/YYYY/MM/DD/tlnet/tlpkg/texlive.tlpdb.xz` walking
     back from today (≤8 days), verifying the **xz magic bytes** — an
     incomplete snapshot answers HTTP 200 with an HTML placeholder (found
     the hard way on 20260926).
  2. fetch + lzma-decompress the tlpdb (~6 MB).
  3. `splitter.partition(packages, "scheme-full", docs=False)` — the same
     first-claim file partition the monolith generator used (each file in
     exactly one group; members = packages whose tarball the group must
     fetch, only when they contributed ≥1 file).
  4. `emit_groups.py` renders the 40 specs; write only byte-changed files;
     append missing `[texlive-<group>] batch = 5` registry entries.
  Output is a pure function of the snapshot date — byte-identical re-runs
  write nothing (idempotence is what makes the workflow's unconditional
  commit safe).
- **The workflow** `.github/workflows/texlive-update.yml`: cron
  `17 04 * * 3` with an ISO-week parity guard (even weeks; first roll week
  40 = 2026-09-30; flip the constant to shift a week), manual dispatch
  always rolls, `--snapshot YYYYMMDD` input to force a date. Commit
  `texlive: roll to tlnet snapshot <date>` + rebase-retry push; the push
  triggers copr-build.yml's batch-5 wave (submit5/wait5 — added).
- **Cascade** `ci/matrix.py`: the batch-floor rule (`batch >= min(changed)`)
  became a **BuildRequires closure** — reverse index over literal BR tokens
  (raw name, `-devel`, `pkgconfig()`/`cmake()` wrapped; macro-wrapped lines
  make that spec conservatively pulled on lower-batch changes). A texlive
  roll now rebuilds only the texlive groups; Monday sweeps stopped
  rebuilding 40 texlive specs. Verified by closure sims (hyprutils → 12
  dependents; texlive-fontsextra → itself; starship → itself).

## Per-group spec model

- No URL Sources — `%build` wgets the group's member tarballs from
  `<snapshot>/tlnet/archive/<pkg>.tar.xz` (tlmgr wire layout) with
  `xargs -P8`, extracts, prunes `texmf-dist/doc` + `texmf-dist/source`
  (the tarballs bundle them; the old staging install ran option_doc/src 0).
  **The docfile set install-tl would install in scheme-full is never
  packaged** (maintainer requirement — no `texlive-doc`).
- Inter-group `Requires: texlive-<other> = %{version}` — the snapshot
  coherence pin (all 40 specs carry the same snapshot Version, so the pin
  is always satisfiable within a roll).
- `texlive-basic` regenerates `texmf-dist/ls-R` in `%build` (install-tl
  used to make it) and claims it in `%files`.
- Carried defines: `debug_package %{nil}`, `__brp_mangle_shebangs %{nil}`,
  `_unpackaged_files_terminate_build 0` (koma-script-class tlpdb drift).
- `emit_groups` refuses to render a group with zero runfiles (would build
  an empty RPM) — investigate before rolling.

## First roll state (20260925)

39 groups, 4,654 member tarballs, 185,587 files. Per-group counts match
the monolith's verified 20260901 partition within snapshot drift
(fontsextra 103,070 vs 103,056; games 2,056 vs 2,055). Idempotence
verified (second run: `unchanged`). All 40 specs rpmspec-parse clean.
Pending: local mock builds of representative groups + the first Copr
build.

## gotchas worth remembering

- **texlive.info fronts the archive with Anubis**: curl/wget-shaped
  User-Agents pass, everything else gets a 200 HTML challenge page. roll.py
  sends a Wget-shaped UA on purpose — do not "clean it up".
- `curl` confirmed the snapshot layout: `tlnet-archive/2026/09/25/tlnet`
  serves the tlpdb.xz; TeX Live 2026 rolls there until the ~March 2027
  freeze.

## Risks / hatch

- texlive.info is one person's infra (probe + build fetch both hit it);
  archive root is a parameter.
- `%files`-from-tlpdb vs tarball drift fails builds loudly — re-roll.
- Engine/format skew vs Fedora's texlive binaries: revert the roll commit;
  Copr keeps the last good build per package.
- Follow-ups (unchanged from the monolith era): texlive-bin, texlive-doc,
  format/map/hyphenation fragments, ls-R scriptlets.
