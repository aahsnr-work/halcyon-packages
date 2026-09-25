# halcyon-packages

Monorepo for the halcyon image — every non-Fedora package the image consumes,
with automated upstream version tracking, built **with anda** (the
terrapkg/packages setup).

Each package lives in `anda/<pkg>/` with an `anda.hcl` manifest, its spec and
a `update.rhai` version sweeper. `anda build` runs every build in a mock
chroot inside `ghcr.io/<owner>/halcyon-builder:f44` (mock, anda, the signing
tooling and the halcyon mock config live in the image), GitHub Actions runs
the waves and publishes, and a GPG-signed dnf repository is served from
GitHub Pages. There is no Copr project, no copr-cli, no FAS account.

- Published repo: `https://aahsnr-work.github.io/halcyon-packages/repo/f44/`
  — enable it with
  `sudo curl -fsSL https://aahsnr-work.github.io/halcyon-packages/repo/f44/halcyon-packages.repo -o /etc/yum.repos.d/halcyon-packages.repo`
- Registry: `ci/packages.toml` — 42 hand packages + the grouped texlive-texmf in 4 dependency batches
- Mock config: `mock/halcyon-f44-x86_64.cfg` (shipped in the builder image)

Setup, migration notes and day-to-day commands: `notes/anda-setup.md`.
Recreating the whole setup from zero (builder image, GPG key, Pages, first
builds): `Instructions.md`. Package/build status: `TODO.md`.

## Layout

| path                 | what                                                                                                                                                                                   |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `anda.hcl`           | root manifest — `strip_prefix`/`strip_suffix`; anda discovers the repo recursively                                                                                                          |
| `anda/<pkg>/`        | one directory per package: `<pkg>.spec`, `anda.hcl` (build config), `update.rhai` (version sweep), plus whatever the spec references (`macros.*`, patches, `.desktop`, helper scripts) |
| `ci/`                | `packages.toml` (dependency-order registry), `matrix.py` (build-matrix generator), `publish.sh` (sign + createrepo + Pages deploy)                                                     |
| `mock/`              | the halcyon mock config: the buildroot definition every build shares                                                                                                                   |
| `.github/builder/`   | the builder image Dockerfile (terrapkg/builder, on Fedora 44)                                                                                                                          |
| `templates/`         | starting points: `anda.hcl.tmpl`, `update.rhai.tmpl`, spec templates                                                                                                                   |
| `repo/`              | the client-side `.repo` file for the Pages repository                                                                                                                                  |
| `tools/`             | helper generators (TeX Live grouped-RPM splitter)                                                                                                                                      |
| `.github/workflows/` | `anda-build.yml` (waves + publish), `anda-publish.yml` (reusable publish job), `anda-update.yml` (daily sweep), `builder-docker.yml` (builder image)                                   |

## How a build happens

1. `anda-build.yml` decides what to build — on a push to `main` that is every
   package whose directory changed since the previous commit, **plus every
   package in a higher batch** (`ci/matrix.py --since <sha>`, terra's
   `anda ci` JSON shape).
2. The manifest job splits the matrix into batch waves (`ci/packages.toml`).
3. `buildN` runs `anda build <pkg> -c halcyon-f44-x86_64` in the builder
   container (privileged, mock backend): mock fetches the spec's URL sources
   and builds the SRPM, then builds the RPMs in the `halcyon-f44-x86_64`
   chroot — Fedora 44 + updates, the published Pages repo, and
   `copr://lionheartp/Hyprland` as a direct baseurl (Fedora 44 lacks
   `glaze-static`, `hyprtoolkit`, `hyprwire`, `wlroots` …).
4. `publishN` downloads the wave's RPMs, signs them (`rpmsign`), regenerates
   repodata (`createrepo_c`), prunes superseded versions and deploys to the
   gh-pages branch — **before the next wave starts**. That publish is what
   lets wave N+1 install wave N's output as BuildRequires, replacing both
   Copr's `--after-build-id` batches and anda's `mock --install_rpms`
   chaining. Pull requests skip publishing (validation only).
5. Batches enforce the dependency order: the waves run sequentially (`needs`
   chain), packages inside one batch build in parallel — they must never
   require each other.

## Build system comparison: anda (this repo) vs Copr (previous)

This repo builds on **anda** with the wave pipeline in `ci/` and publishes
itself; Copr built on **Fedora Copr** custom-source builds. Both produce
ordinary dnf-installable RPMs — the trade-offs that decided the move back:

### anda — this repo's method

| anda                                                                                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------- |
| ✓ Network access inside the build chroot by default — cargo/npm source builds (`%cargo_prep_online`) work without indirection                  |
| ✓ Terra-only macros keep specs terse (`%pkg_completion`, `%terra_appstream`, `%cargo_prep_online`) via `anda-srpm-macros`                      |
| ✓ Self-contained in a plain GitHub repository: builds run in CI containers, no external build-service account needed                           |
| ✓ `mock --install_rpms`-style buildroot control via the mock config (own repo + Hyprland repos are buildroot-level, not per-package)           |
| ✗ You operate the whole publishing pipeline: RPM signing (GPG key handling), `createrepo_c`, and the Pages repo                                |
| ✗ No dependency batching in anda — build order and buildroot inputs are hand-wired per wave in `ci/`                                           |
| ✗ The sweep (`anda update`) commits specs directly in terra's flow — this repo keeps the PR-review gate by wrapping it in a bump PR            |
| ✗ Long builds (browsers, big Rust trees) consume GitHub Actions minutes (the texlive-texmf build is the heavy one; public repos get free standard runners) |

### Copr — the previous method

| Copr                                                                                                                        |
| --------------------------------------------------------------------------------------------------------------------------- |
| ✓ Build farm, GPG signing, repo serving and expiry were Copr's job — no signing key, no createrepo_c, no hosting to run     |
| ✓ Dependency ordering was declarative (batches in `copr/packages.toml`, enforced with `--after-build-id`/`--with-build-id`) |
| ✓ Per-build logs, results directories and status tables (`copr-cli monitor`, `copr/watch.py`) for free                      |
| ✓ Client side was a single dnf repo file (`priority=1`), key served by Copr                                                 |
| ✗ Build chroots default to no network — source-style builds need the source-script indirection or `--enable-net`            |
| ✗ Copr's builder resources/time limits are shared infrastructure — Firefox-class builds run close to the practical limits   |
| ✗ Depends on Copr's infrastructure and its Fedora chroot cadence                                                            |

## Adding or enabling a package

1. `anda/<pkg>/` — `mkdir`, write `<pkg>.spec` from
   `templates/source-build.spec.tmpl` (source build) or
   `templates/binary-wrapper.spec.tmpl` (upstream-binary repack). Constraints
   that bite:
   - use full URLs in `Source*` entries — mock fetches them at SRPM-build
     time; keep downloads out of `%prep` (read files from `%{_sourcedir}` or
     let `%setup -a 0` unpack them);
   - explicit `Release: N%{?dist}` + a written `%changelog` (no rpmautospec);
   - build-time repos other than Fedora/the mock cfg's own repos go in
     `anda.hcl`'s `rpm.extra_repos`.
2. `anda/<pkg>/anda.hcl` — from `templates/anda.hcl.tmpl`.
3. `anda/<pkg>/update.rhai` — from `templates/update.rhai.tmpl` so the daily
   sweep keeps the version fresh.
4. Register it in `ci/packages.toml` with a `batch` that is at least one
   higher than every package it build-requires.
5. Build locally (or push — the workflow picks it up):
   `podman run --rm -it --privileged -v "$PWD":/h -w /h ghcr.io/<owner>/halcyon-builder:f44 anda build <pkg> -c halcyon-f44-x86_64`

Batch rules: batch 0 may only use Fedora + `lionheartp/Hyprland` (in the mock
config) dependencies, and packages inside one batch are built in parallel —
they must never require each other. A package with no `ci/packages.toml`
entry is never built.

## CI

| workflow             | trigger                                                     | does                                                                                                                                             |
| -------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `anda-build.yml`     | push to `main` (`anda/**`, `ci/**`, `mock/**`), PRs, manual | validates (shell/python syntax, registry consistency, build plan), splits the matrix into batch waves, builds each wave, publishes between waves |
| `anda-publish.yml`   | workflow_call (from anda-build)                             | one wave: sign (`rpmsign`), index (`createrepo_c`), prune superseded, deploy gh-pages — PRs: validation only                                     |
| `anda-update.yml`    | daily 04:17 UTC, manual                                     | `anda update` runs every package's `update.rhai`; opens one bump PR                                                                              |
| `builder-docker.yml` | push (`builder/**`, `mock/**`), PRs, manual                 | builds/pushes the builder image                                                                                                                  |

Merging a bump PR is what rebuilds: `anda-build.yml` then builds the bumped
package plus every higher batch. Secrets: `GPG_PRIVATE_KEY` (+ optional
`GPG_PASSPHRASE`) — see `notes/anda-setup.md`.

## Package status

- **Registered (43)** — the Hyprland stack (`hyprutils`, `hyprlang`,
  `hyprwayland-scanner`, `hyprland-protocols`, `hyprland-qt-support`,
  `aquamarine`, `hyprcursor`, `hyprgraphics`, `hyprland-guiutils`,
  `hyprpwcenter`, `hyprshutdown`, `xdg-desktop-portal-hyprland`,
  `hyprland`), noctalia (`noctalia`, `noctalia-greeter-git`), the
  Hyprland-ecosystem apps (`nwg-look`, `qt6ct` — from
  LionHeartP/hyprlandRPM), the binary/tool wrappers (`bun`, `dust`,
  `lazygit`, `pandoc`, `starship`, `yazi`, `zellij`, `zotero`,
  `xwiimote-ng`, `ticktick`, `chafa`, `atuin`, `bat`, `eza`, `pixi`,
  `tealdeer`, `uv`, `cava`, `gnuplot`). The CLI-tool set
  is required to install from this repo even when Fedora/Terra carry the
  same names — the repo file therefore sets `priority=1`. `zotero` and
  `chafa` are full source builds following terrapkg's specs. `bat`, `hyprutils`,
  `hyprland-protocols`, `nwg-look` and `qt6ct` have green local anda builds
  (2026-09-24, see TODO.md); `xwiimote-ng` has never been through a
  validated build — its first anda run is the validation. Every `anda/`
  directory is registered: no candidates, no deferred packages. bazaar and
  bazzite-portal are deliberately NOT built here — they install from COPR
  `ublue-os/packages` and the Terra repo respectively (see TODO.md for the
  provenance research).

## Package sourcing

- **Imports** — build files come from the SCM repos the original COPRs point
  to (`LionHeartP/HyprlandRPM` for the Hyprland stack); their `update.rhai`
  files sweep the matching `hyprwm/*` repos, so bumps arrive through
  `anda-update.yml` like for every other package.
- **Wrappers** — upstream-binary repackages (bun, dust, lazygit, pandoc,
  starship, yazi, zellij, zotero, xwiimote-ng), Arch-PKGBUILD style: mock
  downloads the release artifact at SRPM-build time, the spec repackages it.
- **Source builds** — noctalia, noctalia-greeter-git, hyprland and the
  imported Hyprland libraries build from source tarballs / git archives.

## Details worth knowing

- **Sources fetch at SRPM-build time**: `anda` passes
  `_disable_source_fetch 0` and `--enable-network`, so URL `Source*` entries
  download on the build host and `%prep` never touches the network (the
  repo's reproducibility pattern, kept from the Copr era).
- **The build-time repo** `lionheartp/Hyprland` (direct baseurl in the mock
  config) is what makes `glaze-static`, `hyprtoolkit`, `hyprwire`, `wlroots`
  … available; it is only a build-time input.
- **Signing is ours again**: `ci/publish.sh` signs each wave with the
  `GPG_PRIVATE_KEY` secret's key and serves the public key at
  `repo/RPM-GPG-KEY-halcyon-packages` on Pages; the Copr project key and
  `copr-cli` are gone.
- **rpmautospec**: specs carry explicit `Release:` + changelog (terra's
  convention); the Copr-era hand-rolled expansion (`copr/lib.sh`) is gone.
- **TeX Live**: `tools/texlive-splitter/` generates Arch-style grouped
  specs from a dated snapshot, but its build/publish steps are not wired into
  the anda pipeline (see `TODO.md` — Fedora ships the groups anyway).
