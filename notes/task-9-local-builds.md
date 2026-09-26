# Task 9 — local podman builds: rust set + hyprland stack

Requirement: build rust-based packages, hyprland, hyprland build
dependencies and other hyprland-related packages in a local podman mock
run before the push, one at a time (AGENTS.md rules).

## Setup

- Builder image `localhost/halcyon-builder:f44` (rebuilt after the
  builder-docker.yml changes; `chmod u-s /usr/bin/umount` carried so mock
  teardown works on this kernel).
- `copr-cli mock-config aahsnr-work/halcyon fedora-44-x86_64` →
  `/var/tmp/builds/local-builds/copr.cfg` — the buildroot is now the Copr
  project itself (Fedora 44 + updates + updates-testing, Terra 44, the
  project's own published builds, lionheartp/Hyprland bootstrap).
- Sequential script `/var/tmp/builds/local-builds/build-all.sh`: per
  package `spectool -g` → `rpmbuild -bs` (sources copied live from
  `/h/pkgs/<pkg>` — late-list spec edits are picked up mid-run) →
  `mock -r /state/copr.cfg --enable-network`.
- State under `/var/tmp/builds/local-builds/` (never /tmp); specs read
  from the workspace bind mount at /h.

## Package list (28, build order)

hyprutils hyprlang hyprwayland-scanner hyprland-protocols glaze
hyprland-qt-support aquamarine hyprcursor hyprgraphics hyprwire
xdg-desktop-portal-hyprland noctalia-greeter-git atuin bat dust eza
starship tealdeer texlab yazi zellij zoxide fd-find cliphist hyprland
hyprland-guiutils hyprpwcenter hyprshutdown

Coverage: the complete hyprland dependency closure (batch 0–2 externals +
xdg portal + greeter), all 12 rust source builds, the 4 new/changed
bin-crate wrappers feeding them (zoxide fd-find cliphist), and the
hyprland GUI satellites. texlive-texmf and onlyoffice are excluded —
parked per instruction; their staged fixes ride the cascade.

Note: `/sccache` is not bind-mounted in the copr.cfg (only the real mock
config had that), so rust builds here run with an in-chroot cold cache —
slower, but exactly what Copr's own builders do.

## Results — first pass (17 OK / 2 mock-fail / 9 srpm-miss)

Green (17): hyprutils, hyprlang, hyprwayland-scanner, hyprland-protocols,
glaze, hyprland-qt-support, aquamarine, hyprcursor, hyprgraphics, hyprwire,
xdg-desktop-portal-hyprland, noctalia-greeter-git, texlab, hyprland,
hyprland-guiutils, hyprpwcenter, hyprshutdown — the entire hyprland
closure builds against the exact Copr buildroot, including hyprland itself
and the first-ever build of the task-3 greeter.

Harness bug (9, not spec failures): the script located the freshly built
SRPM with `ls /state/srpm/${pkg}-*.src.rpm`, but nine specs carry
`Name: rust-<pkg>` (atuin bat dust eza starship tealdeer zellij zoxide
fd-find) — the SRPMs were built and then not found; `build-retry.sh`
(written mid-task) discovers the SRPM from rpmbuild's `Wrote:` line
instead.

Real failures (2), both fixed:

- **zoxide / fd-find** — `%files` did not claim `LICENSE.dependencies`
  (guaranteed unpackaged-file failure); fixed mid-run before their queue
  positions. (cliphist's copy of the same fix became moot — see below.)

- **yazi** — `%files`/`%install` used the Terra-only macros
  `%{_hicolordir}` and `%{_appsdir}`, which don't exist in Fedora's
  buildroot ("File must begin with /"). Replaced with the literal
  `%{_datadir}/icons/hicolor` / `%{_datadir}/applications` paths. This is
  a class the task-6 parse audit could not see: the specs parse fine
  wherever the Terra macro set is installed, and only fail where it is
  absent — exactly the Copr buildroot the local run replicates.
- **cliphist** — the task-4 draft assumed Rust from the crates.io 404;
  upstream is **Go** (go.mod / go.mod proxy, go:embed version.txt, no
  Cargo.toml — cargo tree never had a chance). Rewritten as a Go source
  build per the maintainer's pointer to LionHeartP/hyprlandRPM's
  cliphist spec, adapted the nwg-look way (no go2rpm machinery, no
  vendor tarball — module proxy at %build). GPL-3.0-only, wl-clipboard +
  xdg-utils runtime deps carried from LHP/Fedora.

Latent catch outside the run: **noctalia** used three more Terra-only
macros (`%desktop_file_validate` macro call, `%{_appsdir}`, 
`%{_scalableiconsdir}`) and is not even in this run's package list — it
would have failed in the cascade. meson.build confirms the real install
paths (datadir/applications, icons/hicolor/scalable/apps); the spec now
claims those literal paths. noctalia joined the retry list.

## Retry pass — all green

`build-retry.sh` over 12 packages (the user's three first: cliphist
zoxide fd-find, then atuin bat dust eza starship tealdeer zellij yazi
noctalia): **12/12 OK**. Every spec touched by the fixes built clean
against the exact Copr buildroot; starship re-confirmed the inline
prep + cargo-tree license pipeline locally (matching Copr 11035755).

**Task 9 final: 29/29 packages green** (17 first pass + 12 retry;
noctalia joined the list beyond the original 28). Nothing left failing;
the specs are validated for the first cascade.
