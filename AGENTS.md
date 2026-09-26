# AGENTS.md

RPM package monorepo: 50 hand-maintained packages plus the 40 generated
`texlive-*` rolling groups (39 Arch-style collection-group specs +
`texlive-meta`, regenerated per tlnet snapshot — see `tools/texlive-splitter/`),
built on **Fedora Copr**
([aahsnr-work/halcyon](https://copr.fedorainfracloud.org/coprs/aahsnr-work/halcyon/),
chroot `fedora-44-x86_64`) in CI. The repo itself carries only specs, the
registry, the version sweeper and the workflows; Copr owns the build farm,
the GPG signing and the repo hosting (consumers: `dnf copr enable
aahsnr-work/halcyon fedora-44`). Fedora 44 target.

Deep docs (don't duplicate them here): `Instructions.md` (the pre-Copr
from-zero guide, banner-marked historical), `TODO.md` (status). The Copr
project settings and day-to-day commands live in README.md.

## Commands

There is no test suite; verification = the Copr build going green.

```bash
# submit ONE package to Copr (what copr-build.yml's submit jobs do)
spectool -g -C _srpms/<pkg> pkgs/<pkg>/<pkg>.spec
rpmbuild -bs --define "_sourcedir $PWD/_srpms/<pkg>" \
         --define "_srcrpmdir $PWD/_srpms" \
         --define "_specdir $PWD/pkgs/<pkg>" pkgs/<pkg>/<pkg>.spec
copr-cli build --nowait halcyon _srpms/<pkg>-*.src.rpm
copr-cli watch-build <id>; copr-cli status <id>
# (rpmbuild/spectool/cop-cli: run inside the CI image or a fedora:44 container)

# registry consistency + build plan (what CI's validate job runs)
python3 ci/matrix.py --list
python3 ci/matrix.py --list --since <sha>   # what a push would rebuild

# the version sweep (what update.yml runs daily)
GITHUB_TOKEN=$(gh auth token) python3 ci/sweep/sweep.py [--pkg <name>]

# a mock buildroot identical to Copr's, for debugging a failed build locally
copr-cli mock-config aahsnr-work/halcyon fedora-44-x86_64 > /tmp/copr.cfg
mock -r /tmp/copr.cfg <srpm>

# sweeper changes: rerun the equivalence harness (needs the builder
# container — see the verify.py docstring for the podman one-liner)

# the validate job lints the workflows with actionlint (pinned release +
# checksum in copr-build.yml) — run it locally before pushing workflow edits
```

## Non-obvious rules

- **A package without a `ci/packages.toml` entry is never built** — the
  registry is the build selection AND the sweep-feed config. Adding a
  package = 2 files: `pkgs/<pkg>/<pkg>.spec` (from `templates/*.spec.tmpl`)
  and the registry entry (`batch` + `[pkg.updates]` feed). `nwg-look` and
  `qt6ct` are the reference for ecosystem ports from
  [LionHeartP/hyprlandRPM](https://github.com/LionHeartP/hyprlandRPM). The tree lived under `anda/` in the anda
  era and was renamed `pkgs/` on 2026-09-25 — do not resurrect anda; the
  specs are plain RPM.
- **Batches are dependency levels**: a package's `batch` must be ≥ 1 + the
  highest batch of anything it BuildRequires. Packages within one batch
  submit in parallel and must never depend on each other. `copr-build.yml`
  submits wave-by-wave and waits between waves — each successful build is
  immediately visible to the project repo, which is how batch N+1 installs
  batch N's output as BuildRequires. **Batch 3 = noctalia +
  onlyoffice-desktopeditors (+ the hyprtoolkit GUI apps); batch 4 is
  intentionally empty; batch 5 = the 40 texlive rolling groups** (gaps in
  the batch sequence are allowed; empty waves just skip).
- **Spec conventions** (terra-style, differ from Fedora defaults):
  - full URLs in `Source*` entries — the submit job's `spectool -g` fetches
    them before `rpmbuild -bs`; keep downloads out of `%prep` (read from
    `%{_sourcedir}` or `%setup -a 0`). Exception: the texlive group specs
    have no URL Sources and wget their member tarballs from the dated
    snapshot during `%build` (network is on in Copr builds; `wget` is a
    BuildRequire).
  - explicit `Release: N%{?dist}` + a written `%changelog` — no
    rpmautospec/`%autorelease`.
  - **never mention macros textually in comments** — rpm expands macros
    inside comments too; `%gometa` in a comment killed a build (go/forge
    macros are defined in every buildroot). Name them without the `%`.
  - build-time repos outside Fedora/Terra go in the **Copr chroot's repo
    list** (`copr-cli edit-chroot halcyon/fedora-44-x86_64 --repos …`), not
    the spec. Currently configured: Terra 44 (supplies `anda-srpm-macros`
    for the rust specs — NOT in Fedora 44) and `lionheartp/Hyprland`
    (lowest-priority bootstrap only).
  - _*no debug* packages, for any package_* — every spec carries
    `%define debug_package %{nil}`; nothing in the halcyon image consumes
    debug packages.
  - **prebuilt-binary wrappers need `%define debug_package %{nil}`** — a
    foreign binary yields an empty debugsource file list, which fails the
    build (the remaining wrappers — `bun`, `opencode`, the vendor apps —
    carry it). Wrappers are only allowed when upstream itself ships an RPM
    or a self-contained release archive; otherwise the package is a source
    build.
  - **Rust packages build from source with the terra rust2rpm macro set**
    (`anda-srpm-macros` from Terra + `cargo-rpm-macros` from Fedora;
    `starship` is the reference). Don't put the crates.io URL macro in
    `Source:` — spell out the static.crates.io URL (sources are fetched
    before the buildroot macros exist). `-- --locked` on the install macro
    (cargo re-resolution breaks drifted crates), undefine the shebang
    mangler (vendored crate sources trip the debugsource scan), and
    `%define rustflags_debuginfo 0` (no debug packages → debuginfo is pure
    waste). `SCCACHE_DIR=/sccache` works on Copr — the cache is just
    ephemeral per build now (the persistent bind mount was mock-local).
  - `install -t DIR SRC` keeps SRC's basename — `%files` must claim the
    name as installed (bun's completions: `bun.bash` vs `bun` killed a
    build). Prefer explicit `install -Dm644 SRC %{buildroot}%{dir}/NAME`.
  - never use `%forgeautosetup`/`%forgemeta` without defining the forgemeta
    state — without it the archive dir name is derived wrong
    (`distroshelf` lesson). Use plain `%autosetup -n <archive-dir>`.
  - validate a spec against the UPSTREAM tarball, not from memory: release
    layouts drift (cava 1.0.0 dropped its changelog/man page from the
    tarball; bat renamed `completions/` to `autocomplete/`).
  - **Copr's brp hooks are stricter than the old anda buildroot** and hard-
    fail builds anda let pass: the shebang mangler (data-tree specs — the
    texlive groups nil it for their upstream scripts), `check-rpaths`
    (vendor ELFs with hard-coded rpaths) and rpm's `/usr/lib/.build-id`
    link writing (nothing packages them when the debug package is off —
    `%global _build_id_links none`). Vendor rewraps carry the full nil set:
    `obsidian`, `onlyoffice-desktopeditors` and the texlive groups are the
    references. Do not remove those defines.
- **The buildroot is Copr's `fedora-44-x86_64` chroot** — there is no mock
  config in-repo anymore. Buildroot-relevant changes (chroot repos,
  additional packages) are Copr project settings: `copr-cli edit-chroot`.
  Project settings: `--appstream off`, `--enable-net on`, build timeout
  default 5 h (raisable to 50 h — onlyoffice needs ~1 h, the heavy texlive
  groups 20-40 min each). Retention: the
  newest successful build per package is kept, older builds pruned after 14
  days; a failed build never replaces the published one.
- **CI job image** (`.github/builder/Dockerfile`): fedora-minimal 44 +
  copr-cli, python3, rpm-build, rpmdevtools, git, gh, jq — no anda, no
  mock, no signing/publish tooling. Changing it requires a
  `builder-docker.yml` image rebuild before CI jobs work (the validate job
  waits for it automatically).
- **CI authentication**: the `COPR_CLICONF` GitHub secret (content of
  `~/.config/copr`) drives every copr-cli step. **The Copr API token
  expires** — a wave of 401s in copr-build.yml means: regenerate at
  <https://copr.fedorainfracloud.org/api/>, re-set the secret, re-run.
- Touching `ci/**` or `.github/builder/**` makes `ci/matrix.py` rebuild
  _every_ package (`INFRA_PREFIXES`).
- A push to `main` rebuilds changed packages **plus every higher batch**
  (wave-submitted); the same cascade applies to the `only` input of the
  manual `copr-build.yml` run. PRs run validation only (no Copr builds).
- **Version bumps are automatic** (`update.yml`, daily 04:17 UTC):
  `ci/sweep/sweep.py` reads each package's `[pkg.updates]` table
  (`feed = "github-release" | "github-tag" | "custom"` + `repo`) and edits
  specs with the exact old-anda semantics (Version + Release reset only on
  a real version change; `%global` rewrites preserve column formatting;
  file written only on content change). Custom feeds live in
  `ci/sweep/custom.py` (11 hand-ported feed logics; `hyprland`/
  `noctalia-greeter-git` are git-snapshot trackers with `bumpver`/`^N`
  counter semantics). Default mode commits bumps straight to main
  (self-healing: a failed build leaves the published version untouched);
  set the `UPDATE_MODE` repo variable to `pr` for a review gate. After
  touching `ci/sweep/`, rerun `ci/sweep/verify.py` — the harness that
  proved the port against `anda update` (42/46 byte-identical; it also
  documents the four rhai bugs the port fixes).
- `xwiimote-ng` had never been through a validated build until the Copr
  cascade — its first green Copr build closes that item (watch it in
  TODO.md).
- texlive: 40 generated specs (the Arch-style `texlive-<group>` rolling
  groups + `texlive-meta`) are rewritten wholesale per snapshot by the
  biweekly roll — `.github/workflows/texlive-update.yml` (Wednesdays,
  even ISO weeks; manual dispatch always) runs `tools/texlive-splitter/
  roll.py` against the newest `texlive.info/tlnet-archive` daily snapshot.
  They carry no `[pkg.updates]` tables and are never swept; never
  hand-edit them. Their `%build` wgets each group's member tarballs from
  the dated snapshot (no URL `Source` entries — spectool fetches nothing
  for them).
