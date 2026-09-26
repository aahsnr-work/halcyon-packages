# kitty 0.49.1 — new package (source build, adapted from LionHeartP/hyprlandRPM)

Source recipe: LionHeartP/hyprlandRPM's `kitty/kitty.spec` (which tracks
Fedora's kitty packaging). Upstream 0.49.1 is current (Sept 2026, 145
releases); Fedora 44 ships 0.47.1 — our build shadows it via `priority=1`.

## Adaptations from the LHP spec (repo conventions)

- `%autorelease`/`%autochangelog` → explicit `Release: 1%{?dist}` + a
  written changelog.
- Forge/go-vendor machinery dropped: no `go_vendor_archive`, no
  `bundle_go_deps_for_rpm.sh`, no `%gobuild`, no `go-rpm-macros`. The
  `kitten` binary builds with plain `go build ./tools/cmd` (module
  `github.com/kovidgoyal/kitty`, go 1.26 — Fedora 44 has golang 1.26.8),
  modules fetched from the proxy at build time (`GOFLAGS=-mod=mod`,
  `GOTOOLCHAIN=local`), the nwg-look/cliphist pattern. `LDFLAGS` unset for
  the go link (rpm's linker flags break it).
- GPG signature verification (`kovid.gpg` + `.sig` sources) dropped;
  `git-core`/`gnupg2` BRs gone with it.
- The appdata manifest (upstream has none; LHP pulls it from kitty PR
  2088) is carried **in-repo** as `pkgs/kitty/kitty.appdata.xml` (bun's
  metainfo pattern), `Source2`.
- Nerd font pinned: kitty's `setup.py` **hard-fails** on Linux without
  `SymbolsNerdFontMono-Regular.ttf` (fc-list finds nothing in a
  buildroot), so `NerdFontsSymbolsOnly.tar.xz` is a URL source pinned to
  nerd-fonts v3.5.1 (LHP used the moving `releases/latest` URL) and
  extracted into `fonts/` in %prep.
- Tests are not run (repo convention); `%check` keeps
  `appstream-util validate-relax` + `desktop-file-validate`.
- No `kitty-doc` subpackage (repo no-docs convention). Man pages ARE
  built: `make man` (sphinx) after `linux-package` — the man build imports
  the just-built `kitty.fast_data_types` via docs/conf.py, and needs
  `python3-sphinx` + copybutton + design + opengraph extensions (all in
  Fedora 44; conf.py's furo theme is swapped for the builtin classic).

## Subpackages (like LHP/Fedora/Arch)

| subpackage | contents |
|---|---|
| kitty | binary, desktop file, icons, libdir, man pages, appdata |
| kitty-terminfo | noarch `xterm-kitty` terminfo (install standalone on ssh remotes; version must match the terminal) |
| kitty-shell-integration | noarch libdir shell-integration scripts |
| kitty-kitten | the Go `kitten` binary |

Main `Requires:` all three (terminfo/shell-integration pinned to exact
EVR, kitten arch-qualified).

## Registry

`[kitty] batch = 0` (every BuildRequire is Fedora 44) +
`[kitty.updates] feed = "github-release" repo = "kovidgoyal/kitty"` —
upstream releases frequently; the weekly Monday sweep picks each one up
(~10-20 min Copr build per bump).

## Validation

- rpmspec parse clean in the builder container (Name + 3 subpackages).
- Local mock build against the exact Copr buildroot:
  <!-- result appended when the run completes -->
