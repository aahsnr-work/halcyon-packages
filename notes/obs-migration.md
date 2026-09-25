# OBS migration — decision + recipe

Status: **GitHub side done; OBS project applied; push notification wired
via webhook; local OBS-equivalent builds via tools/obs-local.sh; the
network-isolated packages (rust source builds, nwg-look, distroshelf) stay
on the Actions flow (hybrid policy).**

- ✅ GitHub repo pushed with the full project (`60a9f72`, main, public) —
  scmsync builds from it.
- ✅ Migration script: `tools/obs-migrate.py` — generates the project meta
  for project **`halcyon041`** (same name as the OBS user; Fedora 44 target,
  x86_64, publish enabled) and one scmsync package meta per
  `ci/packages.toml` entry (`?subdir=anda/<pkg>#main`), excluding
  texlive-texmf.
- ✅ **Applied**: `home:halcyon041` project with the Fedora_44 repo
  (path = Fedora:44 standard, x86_64, publish on); the obs-scm-bridge
  fetched the `anda/<pkg>` subdirs when the scmsync metas were set.
  Runbook that was used: `osc ls Fedora:44` preflight, then
  `OBS_USER=halcyon041 tools/obs-migrate.py --apply`.
- ✅ **hyprwm external deps — resolved in-repo** (2026-09-25): the
  lionheartp/Hyprland Copr can NOT be attached (download-on-demand is
  admin-gated on the public instance — HTTP 403 on `<download>` in project
  meta). The externals are now packages in this repo instead: glaze 8.4.0
  (batch 0), hyprwire 0.3.1 (batch 1), hyprtoolkit 0.6.0 (batch 2) — ports
  of the Copr's LionHeartP/hyprlandRPM specs, pinned to the NVRs the
  dependents were validated against. The fourth Copr input, wlroots, ships
  in Fedora 44 itself (0.20.2 + devel) and is used straight from there —
  an in-repo port was built once, then removed on the user's call.
  Consumers: hyprland (glaze, hyprwire), hyprshutdown (glaze, hyprtoolkit),
  hyprland-guiutils + hyprpwcenter (hyprtoolkit), noctalia-greeter-git
  (wlroots from Fedora). Everything else builds against Fedora alone
  (nwg-look merely mentions wlroots in its description — audit corrected).
- ✅ **Push → OBS notification wired** (2026-09-25): scmsync does NOT watch
  GitHub — the obs-scm-bridge is a server-side service that only runs when
  notified (verified against bs_srcserver + the OBS user guide). The loop:
  global OBS token `12525` (operation `runservice`,
  `osc token --create --operation runservice` — project-wide runservice
  tokens are not supported) + a GitHub push webhook
  (`https://build.opensuse.org/trigger/webhook?id=12525`, secret = token
  string). Every push notifies OBS; the bridge re-fetches `anda/<pkg>` and
  a rebuild follows only where the fetched revision (srcmd5) actually
  changed, so sweep-PR merges and renames propagate and everything else
  no-ops.
- ✅ **Rebuild policy**: repository rebuild mode stays at the OBS default
  **transitive** (project meta `<repository rebuild="transitive">`) — a
  changed source rebuilds the full build-dependency closure, which is the
  OBS-native replacement of our batch cascade. `osc rebuild --failed
  home:halcyon041` re-triggers failures.
- ⚠️ **Network-isolated packages — hybrid policy**: OBS build VMs prohibit
  network access (obs-docu Security Concepts; obs-build `--vm-network` is
  opt-in), so the rust source builds (cargo fetch in %build), nwg-look (Go
  module proxy) and distroshelf (meson-cargo) can not build on OBS as
  speced; `anda-srpm-macros` is additionally Terra-only (not in Fedora 44 —
  `cargo-rpm-macros`, `sccache`, `mold` are). Those packages keep building
  on the Actions flow; the OBS-native fix later is vendoring
  (obs-service-cargo vendor tarball + offline `cargo_prep`).
- ⏳ After the offline-buildable set goes green on OBS: flip
  `repo/halcyon-packages.repo` to
  `https://download.opensuse.org/repositories/home:/halcyon041/Fedora_44/`
  (the trailing colon is OBS's URL mangling of `home:`) with the project
  GPG key; drop the Actions build workflow's push trigger (keep
  workflow_dispatch + the sweep). texlive-texmf stays on R2 regardless.

## Decision: GitHub, not GitLab

| criterion | GitHub | GitLab |
| --- | --- | --- |
| repo + history + CI today | already here (Actions, gh auth, scripts) | migration cost for nothing |
| OBS scmsync + SCM/CI workflows | supported | supported (equal) |
| RPM repo registry | n/a (OBS serves repos; Pages fallback) | no first-class RPM registry (generic packages only, no repodata) |
| privileged mock runners | not needed (OBS builds) | not needed (OBS builds) |
| PR-build ecosystem | Packit is GitHub-first | weaker |

GitLab only wins if we ever self-host OBS **and** GitLab together; on
hosted services GitHub is strictly better for this repo.

## What changes when packages move to OBS

1. **Builds**: OBS builds each package against a Fedora 44 target from the
   GitHub repo via scmsync — no anda, no Actions build job, no builder
   image. Pushes are notified by the webhook (see above); the bridge lands
   a new `_scmsync.obsinfo` revision and the scheduler rebuilds
   transitively.
2. **Repo serving + signing: GitHub Pages is NOT needed.** OBS publishes
   every project repo at `download.opensuse.org/repositories/home:<user>/…`
   (or a self-hosted URL) with an automatic per-project GPG key — the 1 GB
   Pages budget and ci/publish.sh both drop out. Keep Pages only as a
   fallback channel, or drop it entirely.
3. **Spec files carry over verbatim — except the network-isolated set.**
   `cargo-rpm-macros`, `sccache` and `mold` are in Fedora 44;
   `anda-srpm-macros` is Terra-only. Rust source builds, nwg-look and
   distroshelf need vendored dependencies (obs-service-cargo pattern) to
   ever build on OBS; until then they stay on Actions (hybrid policy).
4. **Batching**: OBS schedules from repository availability (a package's
   deps become visible as built) with transitive rebuilds — replaces our
   batch waves.
5. **sccache bind mount**: OBS workers have no workspace bind — the
   `SCCACHE_DIR=/sccache` export is harmless (ephemeral cache).
   `rustflags_debuginfo 0`, `-- --locked`, the shebang-mangler undefine and
   `%_smp_build_ncpus` carry over (OBS workers set their own ncpu).
6. **texlive-texmf stays on R2**: multi-GB on the shared public
   instance is impolite (disk quotas) and its build would hog shared
   workers; the current self-built R2 flow is the right home for it.
7. **Version sweeps**: unchanged — `anda update` (anda-update.yml) opens
   the daily bump PR; merging it pushes to main, the webhook notifies OBS,
   the bridge re-fetches and the rebuilds run there. No native OBS
   version-bump automation exists (source services run only when
   triggered); the sweep bot is the standard pattern.

## Local OBS-equivalent builds

`tools/obs-local.sh [--faithful] <pkg>` — osc + obs-build in podman against
the home:halcyon041/Fedora_44 build config (server-side buildinfo; same
repos and prjconf as the backend). `--faithful` adds the `--net=none` VM
isolation. Full recipe + limits: `notes/obs-local-builds.md`.
