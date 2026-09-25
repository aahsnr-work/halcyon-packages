# halcyon-packages — status (anda build system, 2026-09-23)

The project moved back from **Fedora Copr** to **anda** (the terrapkg/packages
setup): `anda build` in mock chroots inside the builder container, publishing a
GPG-signed dnf repo to GitHub Pages. Setup steps live in `notes/anda-setup.md`
and the full A-to-Z guide in `Instructions.md`; this file tracks build status
and open work.

The 2026-09-22 audit still holds: every build-breaking defect found in the
tree was fixed and the stale pins were re-swept before the Copr era; the anda
migration re-uses those same specs (sources now fetch at SRPM-build time
instead of through a Copr source script).

## Package matrix — 42 packages + 388 generated texlive packages (`ci/packages.toml`)

Categorized like the registry itself: `desktops` / `apps` / `tools`. Batch
numbers are dependency levels — anda-build.yml runs the waves sequentially and
publishes each wave to the Pages repo before the next starts, and nothing
inside a batch may depend on another member of it (batch 1 holds
`hyprland-qt-support` because it build-requires `hyprlang`; the noctalia pair
and pyprland sit in batch 0 because they only need Fedora packages). A package
without an entry in `ci/packages.toml` is never built.

Checked means: packaging complete, swept by the daily automation (`anda
update` → bump PR → merge → build). Under Copr the tree was fully validated
with `copr/test-source.sh`; under anda the equivalent validation is `anda
build` itself, so unchecked items carry their open work inline.

### desktops — the Hyprland stack, its portals and the noctalia shell — the image's desktop layer

- [x] **aquamarine** (batch 1) — 0.15.1 — source build (hyprwm)
- [x] **hyprcursor** (batch 1) — 0.1.13 — source build (hyprwm)
- [x] **hyprgraphics** (batch 1) — 0.5.1 — source build (hyprwm)
- [x] **hyprland-git** (batch 2) — 0.56.2^58.git<sha> — source build (main-branch pin, the ~15-minute one)
- [x] **hyprland-guiutils** (batch 1) — 0.2.2 — source build (hyprwm)
- [x] **hyprland-protocols** (batch 0) — 0.7.1 — source build (hyprwm, cmake since v0.7.1); **first anda build green (2026-09-24)**
- [x] **hyprland-qt-support** (batch 1) — 0.1.0 — source build (hyprwm)
- [x] **hyprlang** (batch 0) — 0.6.8 — source build (hyprwm)
- [x] **hyprpwcenter** (batch 1) — 0.1.2 — source build (hyprwm)
- [x] **hyprshutdown** (batch 1) — 0.1.1 — source build (hyprwm)
- [x] **hyprutils** (batch 0) — 0.14.2 — source build (hyprwm); **first anda build green (2026-09-24)**
- [x] **hyprwayland-scanner** (batch 0) — 0.4.6 — source build (hyprwm)
- [x] **noctalia-git** (batch 0) — 5.1.0^18.git<sha> — source build (main-branch pin)
- [x] **noctalia-greeter-git** (batch 0) — 1.5.0^8.git<sha> — source build (main-branch pin)
- [x] **pyprland** (batch 0) — 3.4.4 — source build (hatchling wheel + compiled C client, AUR PKGBUILD)
- [x] **xdg-desktop-portal-hyprland** (batch 1) — 1.4.1 — source build (hyprwm)

### apps — vendor and desktop applications the image consumes

- [x] **nwg-look** (batch 0) — 1.1.1 — Go source build (online module proxy at %build; ported from LionHeartP's go2rpm spec); **first anda build green (2026-09-24)**
- [x] **qt6ct** (batch 0) — 0.11 — cmake source build (GitLab commit pin + LHP's shenanigans patch); **first anda build green (2026-09-24)**
- [x] **texlive-texmf** (batch 0) — 20260901 — dated tlnet-archive snapshot, Arch-style groups (noarch data; binaries/fragments are follow-up splits); **first anda build green (2026-09-24)**
- [x] **atuin** (batch 0) — 18.22.0 — wrapper (official gnu tarball)
- [x] **bat** (batch 0) — 0.26.1 — wrapper (man + completions included); **first anda build green (2026-09-24)**
- [x] **bitwarden** (batch 0) — 2026.9.0 — vendor-RPM rewrap (anudeepd spec, byte-identical payload)
- [x] **bun** (batch 0) — 1.4.2 — wrapper (baseline release zip + completions, terrapkg spec)
- [x] **distroshelf** (batch 0) — 1.5.2 — source build (meson + cargo, upstream meson.build)
- [x] **eza** (batch 0) — 0.23.5 — wrapper (man + completions included)
- [x] **obsidian** (batch 0) — 1.13.7 — vendor tarball, Arch package layout; sha256 verified in %prep against the release digest
- [x] **opencode** (batch 0) — 2.0.14 — wrapper (npm release tarball; update.rhai rewrites Source0 when the npm scope moves)
- [x] **pixi** (batch 0) — 0.81.0 — wrapper (official musl binary + completions)
- [x] **tealdeer** (batch 0) — 1.9.0 — wrapper (official musl binary + completions)
- [x] **ticktick** (batch 0) — 8.0.11 — vendor .deb (AUR PKGBUILD); version swept from the AUR RPC
- [x] **uv** (batch 0) — 0.12.17 — wrapper (official musl tarball: uv + uvx + completions)
- [ ] **xwiimote-ng** (batch 0) — 3.0.1 — source build— **open: never built anywhere; the first anda build is its validation**
- [x] **zotero** (batch 0) — 10.0.3 — vendor tarball in terrapkg's spec layout (npm source build dormant: upstream CI artifacts 403)

### tools — the CLI-tool set that must install from this repo even where Fedora/Terra carry the same names (the repo file sets `priority=1`)

- [x] **cava** (batch 0) — 1.0.0 — source build (autotools; ALSA/PipeWire/Pulse/JACK)
- [x] **chafa** (batch 0) — 1.18.2 — source build (autotools, terrapkg spec)
- [x] **dust** (batch 0) — 1.2.6 — wrapper
- [x] **gnuplot** (batch 0) — 6.0.5 — source build (SourceForge, lean cairo/console)
- [x] **lazygit** (batch 0) — 0.65.1 — wrapper
- [x] **pandoc** (batch 0) — 3.11 — wrapper
- [x] **starship** (batch 0) — 1.26.0 — wrapper
- [x] **yazi** (batch 0) — 26.9.1 — wrapper
- [x] **zellij** (batch 0) — 0.45.1 — wrapper

## Validation under anda

The old `copr/test-source.sh` (Copr payload render + SRPM in a container) is
gone; the equivalent is `anda build` itself — the mock backend runs the same
SRPM step and then the full RPM build in the `halcyon-f44-x86_64` chroot. The
buildroot is configured in `mock/halcyon-f44-x86_64.cfg` (shipped inside the
builder image): Fedora 44 + updates, the published Pages repo (own-batch
output), and `lionheartp/Hyprland` for the packages Fedora does not carry.

**First local builds (2026-09-24, builder image built from
`.github/builder/Dockerfile`):**

- ✅ **bat** 0.26.1-1 — wrapper; fixed `autocomplete/` paths (upstream
  renamed the completions dir) + `%define debug_package %{nil}` (prebuilt
  binary → empty debugsource file list)
- ✅ **hyprutils** 0.14.2-1 — cmake source build, full subpackage set
- ✅ **hyprland-protocols** 0.7.1-1 — first package hit by hyprwm's
  meson→cmake migration; converted to `%cmake` + `BuildRequires: cmake`

Notes from the first runs:

- **`target_arch` must be set** in a hand-written mock config — mock's
  default (`i386`) makes every repo metadata fetch 404 on Fedora ≥41.
- The cache plugins (root/yum/ccache) are disabled: state is discarded in
  ephemeral build containers anyway, and their bind mounts break mock's
  chroot cleanup inside containers (EBUSY).
- **Local verification runs under podman, not docker** — on this host the
  Docker default AppArmor/seccomp stack breaks setuid-root `umount` at
  loader time, which silently breaks mock's chroot teardown. GH Actions
  containers (ubuntu kernels) are unaffected — the same flow is what terra
  runs in CI.

## First anda run — order of events

1. `builder-docker.yml` builds and pushes `ghcr.io/<owner>/halcyon-builder:f44`
   (mock, anda, signing tooling and the halcyon mock config live there).
2. The `GPG_PRIVATE_KEY` (+ optional `GPG_PASSPHRASE`) repo secret holds the
   RPM signing key for `ci/publish.sh` (notes/anda-setup.md has the commands).
3. Run `anda-build.yml` with an empty `only`: batch 0 (33 packages) builds,
   publishes to Pages; batch 1 (8 packages) sees it in the buildroot; batch 2
   (`hyprland-git`) last.
4. Watch the Actions run — the wave jobs name their package in the job title.

`xwiimote-ng` has never been through a validated build (neither under Copr nor
here) — treat its first anda build as the validation.

## Open work

- **First full anda run of the registry** (see `Instructions.md` for the
  A-to-Z: builder image, GPG key, Pages enablement, secrets, waves).
- **Bootstrap order**: the mock config points at the (still empty) Pages repo
  with `skip_if_unavailable=True` — build wave 0 and let `ci/publish.sh` seed
  `gh-pages` before the first batch-1 build (the workflow does this
  automatically once the signing key is configured).
- **`hyprtoolkit` / `hyprwire` / `glaze` still come from `lionheartp/Hyprland`**
  at build time — and at _runtime_ for `hyprland-guiutils`, `hyprpwcenter` and
  `hyprshutdown`, which link against `libhyprtoolkit`. Packaging them here would
  make the repository self-contained; until then the image installs them from
  that COPR window.
- **TeX Live — Arch-group packaging, scheme-full, published to R2
  (2026-09-24, final model)**: after trying the per-package rolling model
  (388 specs, one RPM per TL package — shelved; it cluttered the tree and
  the grouped build is the simpler shape), the repo went back to the
  Arch-group spec: ONE source package `texlive-texmf` whose subpackages are
  the collection groups of the scheme (the same direction as Arch's
  texlive-texmf PKGBUILD). Regenerated from the dated tlnet-archive
  snapshot by tools/texlive-splitter (a maintainer step, not a sweep).

  - **Publication: Cloudflare R2 bucket** (`ci/publish-r2.sh`, rclone
    sync, full-snapshot semantics — the set is replaced atomically per
    build). The Pages repo (1 GB budget) keeps the 42 hand packages;
    the [halcyon-texlive] repo section in repo/halcyon-packages.repo
    points at the R2 baseurl. R2 setup: bucket + S3 credentials in the
    secrets (R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY/R2_ENDPOINT), the
    public domain in the R2_LOCAL_HOST/R2_BUCKET variables, and a custom
    domain attached to the bucket in the Cloudflare dashboard.
  - **Scope: scheme-full, no docs** (option_doc 0 — docs are ~70 percent
    of the bulk; the texlive-doc subpackage returns with a large runner).
    Static coverage verified against the tlpdb: 39 subpackages, 185,434
    unique files = the exact install-tl closure (4,226 packages reached;
    zero missing, zero duplicates — the 153 "extras" are koma-script's
    source/... runfiles, whose paths merely contain "/doc/"). The local
    machine's 6 h staging ETA was download-bound — GitHub pulls the same
    payload in 30-40 min, so the CI job is ~1.5-2.5 h total
    (download + install + packaging), inside the standard-runner caps;
    the first real CI run is the end-to-end validation.
  - The bin/x86_64-linux split and the format/map/hyphenation
    post-install fragments remain follow-ups (the halcyon image pairs
    this texmf tree with Fedora's texlive binaries until then).
  - The grouped generator (tools/texlive-splitter) gained --tlpdb-only
    (the %files lists derive from the tlpdb alone — no local staging
    install) and --no-docs. The per-package tools (tools/texlive-pkg)
    were removed with the per-package specs; the old manual-install-style
    rolling diff lives in git history if ever revisited.
    total.
- **`zotero`'s npm source build (terrapkg's spec) is dormant by design**: its
  build.js fetches transient CI artifacts from `zotero-download.s3.amazonaws.com`
  that are 403 for current tags. If upstream ever makes them durable, the spec
  header documents exactly how to restore the full source build.
- **Sweep verification**: the 42 `update.rhai` sweepers have not run
  end-to-end yet — dispatch `anda-update.yml` manually and check the produced
  bump PR before trusting the daily cron (the rhai ports of the
  snapshot-counter packages — hyprland-git, the noctalia pair — carry the
  most logic). Smoke-tested so far: `anda update qt6ct` runs green and
  no-ops on the current pin; the `gh()`-based sweepers need
  `GITHUB_TOKEN` (CI passes `github.token`; the gh() 401 on this box was the
  missing local token).
- **`repo/halcyon-packages.repo`** hard-codes the `aahsnr-work` Pages URL;
  regenerate from `templates/halcyon-packages.repo.tmpl` if the repo lands
  under another owner.

## Provenance research (2026-09-22 / 2026-09-24)

Where the Bazzite image (ublue-os/bazzite, Fedora 44 — same target as this
repo) installs things from:

- **bazaar** (GNOME app store): COPR **`ublue-os/packages`** (enabled in the
  Bazzite Containerfile with priority 98), built from `staging/bazaar/` in
  github.com/ublue-os/packages; published for fedora-44 as 0.9.3-4. NOT in
  Terra, NOT in Fedora. Their recent COPR builds have been failing, so that
  dependency is fragile. If bazaar ever has to come from this repo, a
  candidate matched to upstream v0.9.4 (newer than ublue's published build)
  would need a new `anda/bazaar/` directory and a registry entry.
- **bazzite-portal** (ublue-os/yafti-gtk): packaged by **Terra**
  (terrapkg/packages, `anda/apps/bazzite-portal`, published at
  repos.fyralabs.com/terra44 as 0.2.4-1.fc44 noarch). Bazzite enables Terra
  with `dnf install terra-release` from repos.fyralabs.com/terra$releasever.
  Nothing to build here — enable Terra on the image if it is needed.

The Hyprland ecosystem packages — the hyprwm stack, the noctalia pair,
`xdg-desktop-portal-hyprland` — all originate from
**github.com/LionHeartP/hyprlandRPM**: the specs here are imports of that
repo (pins ride the daily sweep like every other package). Since
2026-09-24 the repo also builds its ecosystem siblings from the same source:
**nwg-look** (as an online-Go build — module proxy at %build time, replacing
LHP's maintainer-generated vendor tarball) and **qt6ct** (their spec + the
qt6ct-shenanigans patch, forgemeta inlined to a GitLab-commit Source0).

Upstream note: hyprwm migrated its build systems from meson to cmake in
mid-2026; `hyprland-protocols` v0.7.1 is the first affected tag (fixed in
these specs — cmake build + `BuildRequires: cmake`); the same conversion
will land in the remaining hyprwm repos over time and the local `anda build`
will catch it per package.

## Repo identity for the 14 always-here CLI tools (plus vendor apps)

atuin, bat, bun, cava, chafa, dust, eza, gnuplot, pixi, starship, tealdeer,
uv, yazi and zellij must install from this repo even where Fedora or Terra
carry the same name. `repo/halcyon-packages.repo` therefore sets
`priority=1` (dnf prefers the repo regardless of version).

## Network access during builds

anda builds with mock network on by default (`anda` passes
`--enable-network` and undefines `_disable_source_fetch`), which is what makes
Terra-style cargo/npm source builds possible — the reason this repo left
Copr's network-off default behind by setting `--enable-net on`. The specs
still keep downloads out of `%prep`: URL sources are fetched at SRPM-build
time by mock, so wrapper builds stay reproducible.

## ticktick automation state

Fully automated since the AUR port: the version sweeps the AUR package via
the AUR RPC API (the AUR maintainer tracks upstream releases), so ticktick
rides the daily sweep and bump PRs like every other package. The spec also
follows the AUR PKGBUILD now: vendor .deb payload (with the desktop file and
icons the vendor RPM lacks), `/usr/bin/ticktick` launcher with user-flags
support, Electron/Chromium license texts relocated, SUID chrome-sandbox.
