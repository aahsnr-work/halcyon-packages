# halcyon-packages — status (Fedora Copr, 2026-09-25)

The project migrated back to **Fedora Copr** (`aahsnr-work/halcyon`,
`fedora-44-x86_64`): CI generates SRPMs from the plain specs (`spectool` +
`rpmbuild -bs`), submits them wave-by-wave (`copr-build.yml`), and Copr
builds, signs and serves the repo. The anda era (mock chroots in a builder
image, GPG-signed Pages + R2 publishing) was removed on 2026-09-25; the
version sweep is now `ci/sweep/sweep.py` (a verified Python port of the 48
`update.rhai` scripts) run weekly (Mondays) by `update.yml`. Setup:
README.md (the Copr project & day-to-day section).

The 2026-09-22 audit still holds: every build-breaking defect found in the
tree was fixed and the stale pins were re-swept; the specs carried through
anda and back to Copr unchanged.

## Package matrix — 91 packages (`ci/packages.toml`): 50 hand-maintained plus the 40 generated texlive rolling groups (+ texlive-meta)

Categorized like the registry itself: `desktops` / `apps` / `tools`. Batch
numbers are dependency levels — copr-build.yml submits the waves
sequentially and waits between them (each successful Copr build is
immediately visible to the project repo), and nothing inside a batch may
depend on another member of it (batch 1 holds `hyprland-qt-support` because
it build-requires `hyprlang`; pyprland sits in batch 0 because it only needs
Fedora packages). A package without an entry in `ci/packages.toml` is never
built.

Checked means: packaging complete, swept by the daily automation
(`update.yml` → bump commit → cascade build). Validation is the Copr build
itself, so unchecked items carry their open work inline.

### desktops — the Hyprland stack, its portals and the noctalia shell — the image's desktop layer

- [x] **aquamarine** (batch 1) — 0.15.1 — source build (hyprwm)
- [x] **hyprcursor** (batch 1) — 0.1.13 — source build (hyprwm)
- [x] **hyprgraphics** (batch 1) — 0.5.1 — source build (hyprwm)

# TODO

---

- [x] **hyprland** (batch 2) — 0.56.2^58.git<sha> — source build; tracks the
  newest upstream `vX.Y.Z-b` bugfix branch (upstream keeps no `stable`
  branch; the sweeper resolves the branch and pins its tip — task 2 note)

---

- [x] **hyprland-guiutils** (batch 1) — 0.2.2 — source build (hyprwm)
- [x] **hyprland-protocols** (batch 0) — 0.7.1 — source build (hyprwm, cmake since v0.7.1); **validated build green (2026-09-24, anda era)**
- [x] **hyprland-qt-support** (batch 1) — 0.1.0 — source build (hyprwm)
- [x] **hyprlang** (batch 0) — 0.6.8 — source build (hyprwm)
- [x] **hyprtoolkit** (batch 2) — 0.6.0 — source build (hyprwm; links the in-repo stack)
- [x] **hyprpwcenter** (batch 1) — 0.1.2 — source build (hyprwm)
- [x] **hyprshutdown** (batch 1) — 0.1.1 — source build (hyprwm)
- [x] **hyprutils** (batch 0) — 0.14.2 — source build (hyprwm); **validated build green (2026-09-24, anda era)**
- [x] **hyprwayland-scanner** (batch 0) — 0.4.6 — source build (hyprwm)

# TODO

---

- [x] **noctalia** (batch 0) — 5.1.0 — source build, release-tracked
  (upstream keeps no stable branch; latest release = stable). v5 is the
  C++/meson shell — no quickshell dependency (that was v4; Terra's
  noctalia-nightly spec is the recipe).

---

- [x] **noctalia-greeter-git** (batch 0) — 1.5.0^8.git<sha> — source build (main-branch pin)
- [x] **pyprland** (batch 0) — 3.4.4 — source build (hatchling wheel + compiled C client, AUR PKGBUILD)
- [x] **xdg-desktop-portal-hyprland** (batch 1) — 1.4.1 — source build (hyprwm)

- [x] **kitty** (batch 0) — 0.49.1 — source build (GPU terminal; LHP recipe
  adapted: online Go modules for kitten, in-repo appdata, pinned nerd font,
  sphinx man pages; terminfo/shell-integration/kitten subpackages; shadows
  Fedora's 0.47.1)

### apps — vendor and desktop applications the image consumes

- [x] **nwg-look** (batch 0) — 1.1.1 — Go source build (online module proxy at %build; ported from LionHeartP's go2rpm spec); **validated build green (2026-09-24, anda era)**
- [x] **qt6ct** (batch 0) — 0.11 — cmake source build (GitLab commit pin + LHP's shenanigans patch); **validated build green (2026-09-24, anda era)**
- [x] **texlive-<group> ×39 + texlive-meta** (batch 5) — 20260925 — the rolling Arch-style group split, regenerated biweekly by the texlive roll workflow (scheme-full, no docs; builds pending validation)
- [x] **atuin** (batch 0) — 18.23.0 — source build (rust, terra macro set)
- [x] **bat** (batch 0) — 0.26.1 — source build (rust); **validated build green (2026-09-24, anda era)**
- [x] **bitwarden** (batch 0) — 2026.9.0 — vendor-RPM rewrap (anudeepd spec, byte-identical payload)
- [x] **bun** (batch 0) — 1.4.2 — wrapper (baseline release zip + completions, terrapkg spec)
- [x] **distroshelf** (batch 0) — 1.5.2 — source build (meson + cargo, upstream meson.build)
- [x] **eza** (batch 0) — 0.23.5 — source build (rust, man + completions included)
- [x] **obsidian** (batch 0) — 1.13.7 — vendor tarball, Arch package layout; sha256 verified in %prep against the release digest
- [x] **opencode** (batch 0) — 2.0.14 — wrapper (npm release tarball; the sweeper rewrites Source0 when the npm scope moves)
- [x] **pixi** (batch 0) — 0.81.0 — wrapper (official musl binary + completions)
- [x] **tealdeer** (batch 0) — 1.9.0 — source build (rust, completions included)
- [x] **ticktick** (batch 0) — 8.0.11 — vendor .deb (AUR PKGBUILD); version swept from the AUR RPC
- [x] **uv** (batch 0) — 0.12.17 — wrapper (official musl tarball: uv + uvx + completions)
- [ ] **xwiimote-ng** (batch 0) — 3.0.1 — source build— **open: never validated; the first green Copr build closes this**
- [x] **zotero** (batch 0) — 10.0.3 — vendor tarball in terrapkg's spec layout (npm source build dormant: upstream CI artifacts 403)

### tools — the CLI-tool set that must install from this repo even where Fedora/Terra carry the same names (pin it image-side — see “Repo identity” below)

- [x] **cava** (batch 0) — 1.0.0 — source build (autotools; ALSA/PipeWire/Pulse/JACK)
- [x] **chafa** (batch 0) — 1.18.2 — source build (autotools, terrapkg spec)
- [x] **dust** (batch 0) — 1.2.6 — source build (rust)
- [x] **gnuplot** (batch 0) — 6.0.5 — source build (SourceForge, lean cairo/console)
- [x] **lazygit** (batch 0) — 0.65.1 — wrapper
- [x] **pandoc** (batch 0) — 3.11 — wrapper
- [x] **starship** (batch 0) — 1.26.0 — source build (rust); **validated build green (2026-09-26, Copr 11035755 — the inline online-cargo prep + cargo-tree license pipeline)**
- [x] **yazi** (batch 0) — 26.9.1 — source build (rust, tag tarball + icons/desktop file)
- [x] **zellij** (batch 0) — 0.45.1 — source build (rust)
- [x] **zoxide** (batch 0) — 0.10.0 — source build (rust; shadows Fedora's 0.9.8 via priority=1)
- [x] **fd-find** (batch 0) — 10.5.0 — source build (rust; shadows Fedora's 10.4.2)
- [x] **cliphist** (batch 0) — 0.7.0 — source build (Go — upstream is Go, not Rust; module proxy at %build)
- [x] **texlab** (batch 0) — 5.26.0 — source build (rust, release tag tarball — crates.io stale upstream)
- [x] **marksman** (batch 0) — 2026.02.08 — wrapper (self-contained .NET release binary + repo LICENSE)

## Validation history

**2026-09-24 (anda era)** — first local builds in the builder image
(`.github/builder/Dockerfile` of the time):

- ✅ **bat** 0.26.1-1 — wrapper; fixed `autocomplete/` paths (upstream
  renamed the completions dir) + `%define debug_package %{nil}` (prebuilt
  binary → empty debugsource file list)
- ✅ **hyprutils** 0.14.2-1 — cmake source build, full subpackage set
- ✅ **hyprland-protocols** 0.7.1-1 — first package hit by hyprwm's
  meson→cmake migration; converted to `%cmake` + `BuildRequires: cmake`

**2026-09-25 (Copr era)** — validation is the Copr build itself; smoke
submissions from the migration day: hyprutils **succeeded** (build
11035212), texlive-texmf and onlyoffice-desktopeditors left parked per
instruction (their staged spec fixes ride the first cascade).

**2026-09-26 (Copr era)** — the rust macro replacement validated
end-to-end: rust-starship **succeeded** (build 11035755) with the inline
online-cargo prep block + inline cargo-tree license pipeline (the first
attempt, 11035734, failed on cargo-to-rpm's hardcoded `--offline`). A
28-package local mock run (rust set + the full hyprland closure) was run
in the builder image before the first cascade — notes/task-9-local-builds.md.

## Bring-up on Copr — order of events

1. `builder-docker.yml` builds and pushes `ghcr.io/<owner>/halcyon-builder:f44`
   (copr-cli, python3, rpm-build, rpmdevtools — no buildroot).
2. The `COPR_CLICONF` repo secret holds the copr-cli API config
   (notes/copr-setup.md has the commands).
3. The project + chroot repos exist (`copr-cli create halcyon …` +
   `edit-chroot`, same doc).
4. Run `copr-build.yml` with an empty `only`: batch 0 (33 packages)
   submits and is waited for; batch 1 (8) sees it in the project repo;
   batches 2–4 follow; batch 4 carries texlive + onlyoffice.
5. Watch the Actions run and the Copr monitor (`copr-cli monitor halcyon`)
   — the wave jobs name their package in the job title.

`xwiimote-ng` had never been through a validated build (neither under the
first Copr era nor under anda) — treat its first green Copr build as the
validation.

## Open work

- **Bring-up status (2026-09-26)**: everything is in place — Copr project
  + chroot repos set, `COPR_CLICONF` secret set, consumer drop-in
  (`repo/halcyon.repo`, priority=1), rust path validated (build 11035755),
  local mock validation run done. Remaining: push (the first cascade rides
  the push-triggered `copr-build.yml`), watch all five waves
  (`copr-cli monitor halcyon`), then a consume test (`dnf copr enable` in
  a fresh F44 container).
- **`hyprtoolkit` / `hyprwire` / `glaze` are packaged in-repo** (batches 0–2)
  — the lionheartp/Hyprland chroot repo is a lowest-priority bootstrap only;
  this item is closed for builds. Runtime: `hyprland-guiutils`,
  `hyprpwcenter` and `hyprshutdown` link `libhyprtoolkit` from the in-repo
  build.
- **TeX Live — Arch-shaped rolling groups (2026-09-26, current model)**:
  the ONE-spec `texlive-texmf` monolith was replaced by **40 separate
  specs** — `pkgs/texlive-<group>/texlive-<group>.spec` for the 39
  Arch-style collection groups + `texlive-meta` (the scheme-full
  catch-all), batch 5. The group names are identical to Arch Linux's
  texlive-* packages, so existing installs upgrade in place.

  - **Rolling release**: `.github/workflows/texlive-update.yml` (biweekly,
    Wednesdays on even ISO weeks; manual dispatch always) runs
    `tools/texlive-splitter/roll.py` — probe the newest daily snapshot of
    `texlive.info/tlnet-archive`, fetch its tlpdb, regenerate all 40 specs,
    commit `texlive: roll to tlnet snapshot <date>`. Writes only changed
    specs; a run against an unchanged snapshot is a no-op.
  - **Scope: scheme-full, no docs** — each group's `%build` wgets ONLY its
    member tarballs (tlmgr wire layout: `<snapshot>/tlnet/archive/<pkg>.tar.xz`,
    parallel xargs) and prunes `doc/` + `source/` after extraction; the
    docfile set install-tl would install is never packaged (no
    `texlive-doc`). Inter-group Requires are version-pinned
    (`= %{version}`) so every installed group stays on one snapshot;
    `texlive-basic` regenerates `texmf-dist/ls-R` in `%build`.
  - **First generated snapshot: 20260925** — 39 groups, 4,654 member
    tarballs, 185,587 files (per-group counts match the old monolith's
    verified 20260901 partition within snapshot drift, e.g. fontsextra
    103,070 vs 103,056). Idempotence verified (second roll: unchanged);
    all 40 specs rpmspec-parse clean. Local mock builds of the groups and
    the first Copr build are the remaining validation.
  - **Cascade**: ci/matrix.py now selects rebuilds by a BuildRequires
    closure (a texlive roll rebuilds only the texlive groups — batch 5,
    one parallel wave; the old batch-floor rule would have rebuilt
    everything). Copr keeps the last good build per group, so a bad roll
    never replaces the published set; revert the roll commit to go back.
  - The bin/x86_64-linux split, texlive-doc and the format/map/hyphenation
    post-install fragments remain follow-ups (the halcyon image pairs this
    texmf tree with Fedora's texlive binaries until then).

- **`zotero`'s npm source build (terrapkg's spec) is dormant by design**: its
  build.js fetches transient CI artifacts from `zotero-download.s3.amazonaws.com`
  that are 403 for current tags. If upstream ever makes them durable, the spec
  header documents exactly how to restore the full source build.
- **Sweep verification — done differently (2026-09-25)**: the 48
  `update.rhai` scripts were ported to `ci/sweep/` (Python) and proven
  equivalent with `ci/sweep/verify.py` — 42/46 byte-identical against real
  `anda update` runs, 3 REVIEW (the rhai scripts crashed before writing:
  hyprland undefined `old_tag`, obsidian `#` comments, and the third
  latent breakage: the rhai fed raw v-prefixed tags where the specs need
  unprefixed values) and 1 intentional fix (xdg-desktop-portal-hyprland's
  sdbus_version: the rhai would have produced a `vv2.3.1` download URL).
  The port also fixes `anda update`'s silent-failure habit (script
  exceptions exited 0) — the sweeper exits 1 and the workflow surfaces it.
  Rerun the harness after any `ci/sweep/` change.
- **Sweep mode**: bumps commit straight to main (self-healing via Copr's
  last-good-build retention). If a review gate is ever wanted, set the
  `UPDATE_MODE` repo variable to `pr`.

## Provenance research (2026-09-22 / 2026-09-24)

Where the Bazzite image (ublue-os/bazzite, Fedora 44 — same target as this
repo) installs things from:

- **bazaar** (GNOME app store): COPR **`ublue-os/packages`** (enabled in the
  Bazzite Containerfile with priority 98), built from `staging/bazaar/` in
  github.com/ublue-os/packages; published for fedora-44 as 0.9.3-4. NOT in
  Terra, NOT in Fedora. Their recent COPR builds have been failing, so that
  dependency is fragile. If bazaar ever has to come from this repo, a
  candidate matched to upstream v0.9.4 (newer than ublue's published build)
  would need a new `pkgs/bazaar/` directory and a registry entry.
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
will land in the remaining hyprwm repos over time and the Copr build
catches it per package.

## Repo identity for the 14 always-here CLI tools (plus vendor apps)

atuin, bat, bun, cava, chafa, dust, eza, gnuplot, pixi, starship, tealdeer,
uv, yazi and zellij must install from this repo even where Fedora or Terra
carry the same name. The checked-in consumer drop-in `repo/halcyon.repo`
carries the Copr baseurl, the project GPG key and **`priority=1`** — with
it installed, every package this repo builds shadows same-named packages
from anywhere else (see notes/task-1-repo-priority.md).

## Network access during builds

Copr builds run with `--enable-net on` on the project, which is what makes
Terra-style cargo/npm source builds possible — the specs still keep
downloads out of `%prep`: URL sources are fetched at SRPM-build time by
the submit job (`spectool -g`), so wrapper builds stay reproducible.

## ticktick automation state

Fully automated since the AUR port: the version sweeps the AUR package via
the AUR RPC API (the AUR maintainer tracks upstream releases), so ticktick
rides the daily sweep and bump PRs like every other package. The spec also
follows the AUR PKGBUILD now: vendor .deb payload (with the desktop file and
icons the vendor RPM lacks), `/usr/bin/ticktick` launcher with user-flags
support, Electron/Chromium license texts relocated, SUID chrome-sandbox.
