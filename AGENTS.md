# AGENTS.md

RPM package monorepo: 42 hand-maintained packages plus the grouped
`texlive-texmf` (one spec, subpackages per TL collection group — see
`tools/texlive-splitter/`), built with
[anda](https://github.com/terrapkg/packages) (mock backend) in CI. Two
publication targets: the hand packages as a GPG-signed dnf repo on **GitHub
Pages** (the 1 GB budget constrains it), and the texlive-texmf set — far
beyond that budget — on a **Cloudflare R2 bucket** (`ci/publish-r2.sh`). No
Copr. Fedora 44 target.

Deep docs (don't duplicate them here): `notes/anda-setup.md` (setup +
day-to-day), `Instructions.md` (recreating from zero), `TODO.md` (status).

## Commands

There is no test suite; verification = building the package.

```bash
# build ONE package locally (same image CI uses)
# (<pkg> is the anda alias for the project key anda/<pkg>/pkg)
podman run --rm -it --privileged -v "$PWD":/h -w /h \
  ghcr.io/aahsnr-work/halcyon-builder:f44 anda build <pkg> -c halcyon-f44-x86_64

# registry consistency + build plan (what CI's validate job runs)
python3 ci/matrix.py --list
python3 ci/matrix.py --list --since <sha>   # what a push would rebuild

# local version sweep (GITHUB_TOKEN avoids API rate limits)
GITHUB_TOKEN=$(gh auth token) anda update

# manual publish of a run's artifacts
GPG_KEY_ID=<fpr> ci/publish.sh rpms srpms      # Pages (hand packages)
GPG_KEY_ID=<fpr> ci/publish-r2.sh rpms srpms   # R2 bucket (texlive-texmf)
```

## Non-obvious rules

- **A package without a `ci/packages.toml` entry is never built** — CI ignores
  the directory. The registry is the dependency-order registry; the build
  config itself lives in `anda/<pkg>/anda.hcl`. Generated texlive specs live
  under `anda/texlive/…` — never hand-edit them (they are generator output;
  see the header of any texlive-*.spec for the regeneration flow).
- **Batches are dependency levels**: a package's `batch` must be ≥ 1 + the
  highest batch of anything it BuildRequires. Packages within one batch build
  in parallel and must never depend on each other. Wave N publishes to the
  Pages repo before wave N+1 builds — dependents install from the published
  repo, so PRs validate against the *last published* state. **Batch 3 =
  texlive-texmf**, its own wave, published to R2 (one atomic spec; a single
  multi-hour build job must not gate the hand packages).
- **Adding a package = 4 files**: `anda/<pkg>/<pkg>.spec` (from
  `templates/source-build.spec.tmpl` or `binary-wrapper.spec.tmpl`),
  `anda/<pkg>/anda.hcl` (from `templates/anda.hcl.tmpl`),
  `anda/<pkg>/update.rhai` (from `templates/update.rhai.tmpl`, or the daily
  sweep won't bump it), and the `ci/packages.toml` entry. nwg-look and qt6ct
  are the reference for ecosystem ports from
  [LionHeartP/hyprlandRPM](https://github.com/LionHeartP/hyprlandRPM) (the
  source of the whole hyprwm/noctalia/xdg-portal set).
- **Spec conventions** (terra-style, differ from Fedora defaults):
  - full URLs in `Source*` entries — mock fetches them at SRPM-build time;
    keep downloads out of `%prep` (read from `%{_sourcedir}` or `%setup -a 0`).
  - explicit `Release: N%{?dist}` + a written `%changelog` — no
    rpmautospec/`%autorelease`.
  - **never mention macros textually in comments** — rpm expands macros
    inside comments too; `%gometa` in a comment killed a build (go/forge
    macros are defined in every buildroot). Name them without the `%`.
  - build-time repos outside Fedora go in the package's `anda.hcl`
    `rpm.extra_repos`, not the spec.
  - **no debug* packages, for any package** — every spec carries
    `%define debug_package %{nil}` (one line kills both the debuginfo and
    debugsource subpackages), source builds included: debuginfo generation
    significantly slows every build and the Pages budget has no room for the
    output, and nothing in the halcyon image consumes debug packages.
  - **prebuilt-binary wrappers need `%define debug_package %{nil}`** — a
    foreign binary yields an empty debugsource file list, which fails the
    build (the remaining wrappers — `bun`, `opencode`, the vendor apps —
    carry it). Wrappers are only allowed when upstream itself
    ships an RPM; otherwise the package is a source build.
  - **Rust packages build from source with the terra rust2rpm macro set**
    (`anda-srpm-macros` + `cargo-rpm-macros`, both in Fedora 44):
    `rust-<name>.spec` from terrapkg's `anda/langs/rust/` spec, crates.io
    source via the `terra_crates_source` macro, `cargo_prep_online`,
    `cargo_license_online` for `LICENSE.dependencies`, `-devel` +
    feature subpackages (`starship` is the reference). Don't put that macro
    in `Source:` — mock fetches sources before the buildroot macros exist
    (starship lesson); spell out the static.crates.io URL there. Two more
    hard-won rules, carried by every rust spec here: pass `-- --locked` to
    the install macro — without it cargo re-resolves the dependency graph
    ignoring upstream's Cargo.lock, and drifted crates fail to compile (eza
    palette_derive, atuin's locked-tripwire); and undefine the shebang
    mangler — vendored crate sources ship Rust inner attributes that the
    debugsource scan misreads as shebangs. Crates.io source must exist for
    the crate (pixi/yazi don't publish theirs; they take the GitHub tag
    tarball + cargo_build instead, terra's own style). Rust builds also run
    through **sccache with a workspace-persistent cache**: specs BuildRequire
    sccache, use `cargo_prep_online_sccache`, and `export SCCACHE_DIR=/sccache`
    in both build and install — the mock config bind-mounts
    `/h/anda-build/sccache-cache` there, so the cache survives across
    container runs and is shared by every rust build (verified against mock
    6.8; the historical EBUSY teardown concern does not reproduce because
    nspawn isolation kills chroot processes before mock unmounts). And
    `%define rustflags_debuginfo 0` — with no debug packages shipped,
    generating debuginfo is pure compile-time waste (`build_rustflags`
    composes it from `rustflags_debuginfo`, so one define removes it from
    both RUSTFLAGS and the cargo rpm profile).
  - `install -t DIR SRC` keeps SRC's basename — `%files` must claim the name
    as installed (bun's completions: `bun.bash` vs `bun` killed a build).
    Prefer explicit `install -Dm644 SRC %{buildroot}%{dir}/NAME`.
  - never use `%forgeautosetup`/`%forgemeta` without defining the forgemeta
    state — without it the archive dir name is derived wrong
    (`distroshelf` lesson). Use plain `%autosetup -n <archive-dir>`.
  - validate a spec against the UPSTREAM tarball, not from memory: release
    layouts drift (cava 1.0.0 dropped its changelog/man page from the
    tarball; bat renamed `completions/` to `autocomplete/`).
- **The buildroot is `mock/halcyon-f44-x86_64.cfg`** (Fedora 44 + updates, the
  published Pages repo, the R2 `[halcyon-texlive]` repo, and
  `copr://lionheartp/Hyprland` as a direct baseurl — that Copr supplies
  `glaze-static`, `hyprtoolkit`, `hyprwire`, `wlroots`…).
  It ships inside the builder image: changing `mock/**` or
  `.github/builder/**` requires a `builder-docker.yml` image rebuild before
  builds work.
- **Builds are capped at -j12** — `%_smp_build_ncpus` is pinned to 12 in the
  mock config; every package derives its parallelism from that one macro
  (cargo's `-j`, cmake/meson's `%_smp_mflags`, …). Don't set `-j` per-spec.
- Touching `ci/`, `mock/`, `.github/builder/` or the root `anda.hcl` makes
  `ci/matrix.py` rebuild *every* package (see `INFRA_PREFIXES` there).
- A push to `main` rebuilds changed packages **plus every higher batch**;
  the same cascade applies to the `only` input of the manual workflow run.
- Version bumps are automatic (`anda-update.yml` opens one daily bump PR;
  sweepers are `update.rhai` scripts using andax globals `gh()`,
  `rpm.version()` … — see `templates/update.rhai.tmpl` for the API). Merging
  the bump PR is what triggers the rebuild.
- **Local builds run strictly ONE AT A TIME** (`podman`, never docker —
  docker's AppArmor/seccomp stack breaks setuid-root `umount` at loader time,
  which silently breaks mock's chroot teardown on some host kernels).
  State/logs live under `/var/tmp/builds/` (never `/tmp` — session restarts
  wipe it). Building dependent batches locally: `createrepo_c` over
  `anda-build/rpm/rpms`, then `anda build <pkg> -c halcyon-f44-x86_64 -R
  file:///h/anda-build/rpm`.
- `xwiimote-ng` has never been through a validated build — its first run is
  the validation; watch it.
- texlive: the grouped spec is regenerated per snapshot by
  `tools/texlive-splitter` (`--tlpdb-only`, `--no-docs` — a maintainer step,
  not a sweep); the R2 flow needs the `R2_*` secrets/variables listed in
  `notes/anda-setup.md`.
