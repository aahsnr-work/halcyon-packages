# OBS migration — decision + recipe

Status: **GitHub side done; OBS side pending one token.**

- ✅ GitHub repo pushed with the full project (`60a9f72`, main, public) —
  scmsync builds from it.
- ✅ Migration script: `tools/obs-migrate.py` — generates the project meta
  for project **`halcyon041`** (same name as the OBS user; Fedora 44 target,
  x86_64, publish enabled, lionheartp/Hyprland Copr attached as a
  download-on-demand repo) and one scmsync package meta per
  `ci/packages.toml` entry (`?subdir=anda/<pkg>#main`), excluding
  texlive-texmf. Dry-runs clean (41 packages).
- ✅ **Applied**: `home:halcyon041` project with the Fedora_44 repo
  (path = Fedora:44 standard, x86_64, publish on) and 41 scmsync packages;
  the obs-scm-bridge fetched the `anda/<pkg>` subdirs immediately. Runbook
  that was used: `osc ls Fedora:44` preflight, then
  `OBS_USER=halcyon041 tools/obs-migrate.py --apply`.
- ⚠️ **Known gap — hyprwm external deps**: the lionheartp/Hyprland Copr
  can NOT be attached (download-on-demand is admin-gated on the public
  instance — HTTP 403 on `<download>` in project meta). Fedora 44 lacks
  glaze-devel, hyprtoolkit, hyprwire and wlroots, so six packages fail
  BuildRequire resolution until those four are packaged in the project:
  hyprshutdown (glaze-devel, hyprtoolkit), hyprland-guiutils +
  hyprpwcenter (hyprtoolkit), hyprland-git (hyprwire),
  noctalia-greeter-git + nwg-look (wlroots). Everything else builds
  against Fedora alone.
- ⏳ After first builds go green: flip `repo/halcyon-packages.repo` to
  `https://download.opensuse.org/repositories/home:/halcyon041/Fedora_44/`
  (the trailing colon is OBS's URL mangling of `home:`) with the project
  GPG key, then retire the Actions build workflow (keep the sweep —
  merging its bump PRs to main is what triggers OBS rebuilds).

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
   image. `obs-scm-bridge` watches the repo; a new tag/commit triggers the
   rebuild automatically.
2. **Repo serving + signing: GitHub Pages is NOT needed.** OBS publishes
   every project repo at `download.opensuse.org/repositories/home:<user>/…`
   (or a self-hosted URL) with an automatic per-project GPG key — the 1 GB
   Pages budget and ci/publish.sh both drop out. Keep Pages only as a
   fallback channel, or drop it entirely.
3. **Spec files carry over verbatim** — the terra macro set
   (`anda-srpm-macros`, `cargo-rpm-macros`, `sccache`) is in Fedora 44, so
   OBS Fedora buildroots resolve all BuildRequires from Fedora repos.
   Exception: the lionheartp/Hyprland Copr repo must be added as an OBS
   project repository path for the hyprwm set.
4. **Batching**: OBS schedules from repository availability (a package's
   deps become visible as built) — replaces our batch waves.
5. **sccache bind mount**: OBS workers have no workspace bind — the
   `SCCACHE_DIR=/sccache` export is harmless (ephemeral cache) or strip it
   for OBS; `rustflags_debuginfo 0`, `-- --locked`, the shebang-mangler
   undefine and `%_smp_build_ncpus` all carry over (OBS workers set their
   own ncpu — control via project config `BuildFlags: jobs`? verify).
6. **texlive-texmf stays on R2**: multi-GB on the shared public
   instance is impolite (disk quotas) and its build would hog shared
   workers; the
   current self-built R2 flow is the right home for it.
7. **Version sweeps**: `anda update` / update.rhai becomes a small GitHub
   Action that pushes bump commits (bump tag + spec Version); OBS rebuilds
   automatically — same sweep logic, different transport.

## Execution steps (when credentials exist)

1. `osc` + token; create the `halcyon041` project, add Fedora 44 +
   updates repo path + lionheartp/Hyprland baseurl.
2. Per hand package: `osc meta pkg ... -e` with `scmsync =
   https://github.com/aahsnr-work/halcyon-packages#<tag>` (one scmsync
   target per package directory — or project-wide scmsync with per-package
   subdirs, matching our `anda/<pkg>` layout).
3. First builds green → flip `repo/halcyon-packages.repo` to the OBS
   download URL; retire the Actions build workflow (keep the sweep).
4. Decide Pages: fallback channel or delete.
