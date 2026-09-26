# halcyon-packages

Monorepo for the halcyon image — every non-Fedora package the image consumes,
with automated upstream version tracking, built on **Fedora Copr**
([aahsnr-work/halcyon](https://copr.fedorainfracloud.org/coprs/aahsnr-work/halcyon/)).

Each package lives in `pkgs/<pkg>/` with a plain
RPM spec and whatever the spec references (`macros.*`, patches, `.desktop`,
helper scripts). GitHub Actions generates the SRPMs (`spectool` +
`rpmbuild -bs`), submits them to Copr wave-by-wave, and a sweeper
(`ci/sweep/`) bumps spec versions from upstream feeds — a merged bump (or an
automatic one) lands in the Copr repo without manual steps. Copr owns the
build farm, the GPG signing and the repo hosting; there is no Pages repo, no
R2 bucket, no self-run publishing.

- Enable the repo: `sudo dnf copr enable aahsnr-work/halcyon fedora-44`
- **Priority**: consumers should install `repo/halcyon.repo` (or merge its
  `priority=1` into the copr-plugin-generated file) so everything this repo
  builds — the hyprwm stack, glaze/hyprwire/hyprtoolkit, chafa, the CLI
  tools — always wins over Fedora, Terra and unprioritized Coprs
- Registry: `ci/packages.toml` — 51 hand packages + the 40 generated
  texlive rolling groups in 5 dependency batches, sweep feeds under each
  package's `[pkg.updates]` (the texlive groups have none — the biweekly
  roll owns them)
- Copr project settings and day-to-day commands: below ("Copr project
  & day-to-day"); package/build status: `TODO.md`

## Layout

| path                 | what                                                                                                                                              |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pkgs/<pkg>/`        | one directory per package: `<pkg>.spec` plus whatever the spec references (patches, metainfo, helper scripts, macros)                             |
| `ci/`                | `packages.toml` (dependency-order registry + sweep feeds), `matrix.py` (build-matrix generator), `sweep/` (the version sweeper)                    |
| `ci/sweep/`          | `sweep.py` (engine), `feeds.py` (GitHub/URL feeds), `custom.py` (the 10 feed logics), `spec.py`/`vercmp.py` |
| `.github/builder/`   | the CI job image (fedora-minimal 44 + copr-cli, python3, rpm-build, rpmdevtools)                                                                   |
| `templates/`         | starting points for specs: `source-build.spec.tmpl`, `binary-wrapper.spec.tmpl`, `meta-group.spec.tmpl`, `python-hatchling.spec.tmpl`              |
| `tools/`             | helper generators (TeX Live grouped-RPM splitter)                                                                                                  |
| `.github/workflows/` | `copr-build.yml` (SRPM gen + wave-submission), `update.yml` (sweep, chained to the cascade + weekly floor), `texlive-update.yml` (biweekly roll), `repoclosure.yml` (closure check), `builder-docker.yml` (CI image) |

## How a build happens

1. A push to `main` (spec change, bump commit, or registry/infra change)
   triggers `copr-build.yml`.
2. `ci/matrix.py --since <sha>` selects every package whose directory changed,
   **plus every package in a higher batch**, and splits them into batch waves.
3. `submitN` builds each wave's SRPMs (`spectool -g` downloads the spec's URL
   sources; `rpmbuild -bs` packs them — the old anda SRPM-fetch step, now
   explicit) and submits them with `copr-cli build --nowait halcyon`.
4. `waitN` follows the wave's Copr builds and fails the run if any build
   failed. Each successful build is visible to the project repo immediately —
   that is what lets wave N+1 install wave N's output as BuildRequires (the
   job the old Pages publish used to do). Pull requests stop at the validate
   job (syntax + registry checks; no Copr builds).
5. Batches enforce the dependency order: the waves run sequentially (`needs`
   chain), packages inside one batch build in parallel on Copr — they must
   never require each other.

## How a version bump happens

1. `update.yml` runs chained after every cascade and weekly (Mondays 04:17 UTC): `ci/sweep/sweep.py` asks each
   package's configured feed (`[pkg.updates]` in `ci/packages.toml`) for the
   latest upstream version and edits the spec — `Version:` + `Release:` reset
   to 1, `%global` pins, occasionally a `Source*` rewrite. Specs are written
   only when content actually changed.
2. Default mode (`commit`): the bumps are committed straight to `main` as
   `bump: <date> (<pkgs>)`, and the push triggers `copr-build.yml` for the
   changed packages + every higher batch. Upstream release → Copr repo,
   fully automatic; a failed build leaves the published version untouched
   (Copr serves the newest *successful* build per package), so bad bumps
   self-heal.
3. Review-gate mode (`pr`): set the `UPDATE_MODE` repository variable (or
   pick it in the manual dispatch) and the bumps land on one `bump/<date>`
   branch + a single PR instead.

The sweep logic was ported 1:1 from the old `update.rhai` scripts (proven
against real `anda update` runs while anda still existed — 42/46 packages
byte-identical); the harness itself was retired with the anda tooling.

## Adding or enabling a package

1. `pkgs/<pkg>/` — `mkdir`, write `<pkg>.spec` from
   `templates/source-build.spec.tmpl` (source build) or
   `templates/binary-wrapper.spec.tmpl` (upstream-binary repack). Constraints
   that bite:
   - use full URLs in `Source*` entries — the CI SRPM step (`spectool -g`)
     fetches them before `rpmbuild -bs`; keep downloads out of `%prep` (read
     files from `%{_sourcedir}` or let `%setup -a 0` unpack them);
   - explicit `Release: N%{?dist}` + a written `%changelog` (no rpmautospec);
   - `%define debug_package %{nil}` — no debug* packages, ever;
   - build-time repos outside Fedora/Terra go in the **Copr chroot's** repo
     list (`copr-cli edit-chroot halcyon/fedora-44-x86_64 --repos …`), not
     the spec.
2. Register it in `ci/packages.toml` with a `batch` at least one higher than
   every package it build-requires, and an `[pkg.updates]` feed so the
   sweep keeps the version fresh (`feed = "github-release"` / `"github-tag"`
   with `repo = "owner/name"`, or `feed = "custom"` + a function in
   `ci/sweep/custom.py` for nontrivial feeds).
3. Submit it: push (the workflow picks it up) or locally (see
   "Copr project & day-to-day" below).

Batch rules: batch 0 may only use Fedora + Terra + `lionheartp/Hyprland`
(chroot repos) dependencies, and packages inside one batch are built in
parallel — they must never require each other. A package with no
`ci/packages.toml` entry is never built.

## Copr project & day-to-day

The project lives at [aahsnr-work/halcyon](https://copr.fedorainfracloud.org/coprs/aahsnr-work/halcyon/)
(chroot `fedora-44-x86_64`). Recreating it from zero:

```bash
copr-cli create halcyon \
  --chroot fedora-44-x86_64 \
  --appstream off \
  --enable-net on \
  --description "RPM repository for the halcyon image: hand-maintained Fedora 44 packages (hyprwm stack, CLI tools, the rolling texlive groups), built from github.com/aahsnr-work/halcyon-packages." \
  --instructions "Enable with: dnf copr enable aahsnr-work/halcyon fedora-44
Then install, e.g.: sudo dnf install hyprland"

# build-time repos: Terra 44 (buildroot extras some specs rely on) +
# lionheartp/Hyprland (lowest-priority bootstrap only)
copr-cli edit-chroot halcyon/fedora-44-x86_64 --repos \
  "https://repos.fyralabs.com/terra44 \
   https://download.copr.fedorainfracloud.org/results/lionheartp/Hyprland/fedora-44-x86_64/"
```

Day-to-day (all of this is what `copr-build.yml` does per package; run it
inside the CI image or a fedora:44 container):

```bash
# submit ONE package and follow it
spectool -g -C _srpms/<pkg> pkgs/<pkg>/<pkg>.spec
rpmbuild -bs --define "_sourcedir $PWD/_srpms/<pkg>" \
         --define "_srcrpmdir $PWD/_srpms" \
         --define "_specdir $PWD/pkgs/<pkg>" pkgs/<pkg>/<pkg>.spec
copr-cli build --nowait halcyon _srpms/<pkg>-*.src.rpm
copr-cli watch-build <id>; copr-cli status <id>

# the whole project at a glance / what a push would rebuild
copr-cli monitor halcyon
python3 ci/matrix.py --list --since <sha>

# a mock buildroot identical to Copr's, for debugging a failed build locally
copr-cli mock-config aahsnr-work/halcyon fedora-44-x86_64 > /tmp/copr.cfg
mock -r /tmp/copr.cfg _srpms/<pkg>-*.src.rpm
```

Project semantics: build timeout default 5 h (raisable to 50 h — onlyoffice
needs ~1 h), builds have network (the texlive groups wget their member
tarballs at `%build`),
and Copr keeps the newest *successful* build per package while pruning older
ones after 14 days — a failed build never replaces the published version.

## CI

| workflow             | trigger                                                        | does                                                                                                                       |
| -------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `copr-build.yml`     | push to `main` (`pkgs/**`, `ci/**`), PRs, manual (`only` input) | validates (syntax, registry consistency, build plan, actionlint), splits the matrix into batch waves, submits SRPMs, waits per wave |
| `update.yml`         | chained after every cascade + weekly floor, manual (`mode`, `pkg`) | `ci/sweep/sweep.py` bumps specs from upstream feeds; commits to main (default) or opens one bump PR                        |
| `builder-docker.yml` | push (`.github/builder/**`), PRs, manual                        | builds/pushes the CI job image (copr-cli, python3, rpm tooling — no buildroot: Copr owns the chroots)                       |

Secrets: `COPR_CLICONF` (the copr-cli API config; the token expires after
**180 days**, so calendar the renewal). No GPG or R2 secrets — signing is
Copr's per-project key.

## Package status

- **Registered (50 + 40 texlive groups)** — the Hyprland stack (`hyprutils`,
  `hyprlang`, `hyprwayland-scanner`, `hyprland-protocols`,
  `hyprland-qt-support`, `aquamarine`, `hyprcursor`, `hyprgraphics`,
  `hyprland-guiutils`, `hyprpwcenter`, `hyprshutdown`, `hyprtoolkit`,
  `xdg-desktop-portal-hyprland`, `hyprland`), noctalia (`noctalia`,
  `noctalia-greeter-git`), the
  Hyprland-ecosystem apps (`nwg-look`, `qt6ct` — from
  LionHeartP/hyprlandRPM), the binary/tool wrappers (`bun`, `dust`,
  `lazygit`, `pandoc`, `starship`, `yazi`, `zellij`, `zotero`,
  `xwiimote-ng`, `ticktick`, `chafa`, `atuin`, `bat`, `eza`, `pixi`,
  `tealdeer`, `uv`, `cava`, `gnuplot`, and the rest of the CLI set), the
  batch-4 heavy (`onlyoffice-desktopeditors`) and the 40 batch-5 texlive
  rolling groups. The CLI-tool set is
  required to install from this repo even when Fedora/Terra carry the same
  names — with Copr that is a `dnf copr enable` + `priority` question, see
  the image-side repo config. bazaar and bazzite-portal are deliberately NOT
  built here — they install from COPR `ublue-os/packages` and the Terra repo
  respectively (see TODO.md for the provenance research).

## Package sourcing

- **Imports** — build files come from the SCM repos the original COPRs point
  to (`LionHeartP/hyprlandRPM` for the Hyprland stack); their feeds sweep the
  matching `hyprwm/*` repos, so bumps arrive through `update.yml` like for
  every other package.
- **Wrappers** — upstream-binary repackages (bun, dust, lazygit, pandoc,
  starship, yazi, zellij, zotero, xwiimote-ng), Arch-PKGBUILD style: the CI
  SRPM step downloads the release artifact, the spec repackages it.
- **Source builds** — noctalia-greeter-git, hyprland and the imported
  Hyprland libraries build from source tarballs / git archives.

## Details worth knowing

- **Sources fetch at SRPM-build time**: full-URL `Source*` entries are
  downloaded by `spectool -g` in the submit job (the repo's reproducibility
  pattern, kept from the anda era). The texlive group specs are the
  exception that proves the rule: they have no Source URLs and wget their
  member tarballs from the dated snapshot **during `%build`** — Copr builds
  have network, `wget` is a BuildRequire.
- **Rust builds**: the 10 rust specs BuildRequire `anda-srpm-macros` (Terra
  repo — not in Fedora 44) and `sccache` (Fedora). The sccache cache is
  ephemeral per Copr build (the old `/sccache` bind mount was mock-local);
  it still works, it just no longer persists across builds.
- **Signing is Copr's**: every build is signed with the project's own GPG
  key, served through the standard `dnf copr enable` flow. The hand-managed
  key, `repo_gpgcheck` and the signed-repomd dance are gone with the Pages
  pipeline.
- **Copr's brp hooks run stricter than the old anda buildroot** — three of
  them hard-fail builds that anda let pass: the shebang mangler (texlive's
  185k upstream scripts), `check-rpaths` (onlyoffice's vendor ELFs with
  hard-coded Qt rpaths) and rpm's `/usr/lib/.build-id` link writing (the
  same vendor blob). Affected specs carry targeted `%global ... %{nil}`
  defines — `obsidian`, `onlyoffice-desktopeditors` and `texlive-texmf` are
  the references; don't strip them from rewrap/data-tree specs.
- **GCC 16 and the hyprwm generated code**: gcc 16.2.1 turned the empty
  vtable arrays in hyprwm's wayland-scanner-generated C++ (aquamarine's
  `protocols/wayland.cpp` et al.) from pedantic warnings into hard errors —
  while the packages' own `-Wpedantic` is still in their CMake flags. The
  affected specs strip the flag (`sed -i 's/-Wpedantic//' CMakeLists.txt`)
  until upstream ships gcc-16 clean releases; a build that passed at 08:00
  and fails at 15:00 is this, not a spec regression.
- **TeX Live rolls biweekly**: `tools/texlive-splitter/roll.py` (driven by
  `.github/workflows/texlive-update.yml`, Wednesdays on even ISO weeks;
  manual dispatch always) regenerates the 40 Arch-style group specs
  (`texlive-<group>` + `texlive-meta`) from the newest
  `texlive.info/tlnet-archive` daily snapshot — scheme-full, no docs. The
  groups carry no updates tables and are never swept; a roll commit lands
  with the message `texlive: roll to tlnet snapshot <date>` and the push
  rebuilds the changed groups as the batch-5 wave. To roll manually:
  `gh workflow run texlive-update.yml` (or a local `python3
  tools/texlive-splitter/roll.py`).

## Recreating this repository from scratch

Strict order — **the `COPR_CLICONF` secret must exist before the first
content push** (the push triggers the full Copr cascade, which cannot
authenticate without it). Prerequisites: a Fedora box or container with
`dnf`, plus `git`, `gh` and `curl`.

1. **Copr account** — create a Fedora account at
   <https://accounts.fedoraproject.org/>, then log in at
   <https://copr.fedorainfracloud.org/> with **OIDC login** (that is the
   FAS login; `gssapi` is the Kerberos variant). The first login asks for a
   ~6-month-old GitHub account as an anti-abuse check.
2. **API token** — install copr-cli and store the token:

   ```bash
   sudo dnf install copr-cli
   # log in at https://copr.fedorainfracloud.org/ then open
   # https://copr.fedorainfracloud.org/api/ and copy the config snippet into:
   mkdir -p ~/.config && $EDITOR ~/.config/copr
   chmod 600 ~/.config/copr
   copr-cli whoami          # must print your Copr login
   ```

   The token expires after **180 days** — 401/403 waves in copr-build.yml
   mean regenerate at `/api/` and re-run step 3.
3. **GitHub secret**:

   ```bash
   gh auth login
   gh secret set COPR_CLICONF --repo OWNER/NAME < ~/.config/copr
   ```

4. **Create the Copr project + chroot repos**:

   ```bash
   copr-cli create halcyon \
     --chroot fedora-44-x86_64 \
     --appstream off \
     --enable-net on \
     --description "RPM repository for the halcyon image: hand-maintained Fedora 44 packages (hyprwm stack, CLI tools, the rolling texlive groups), built from github.com/OWNER/NAME." \
     --instructions "Enable with: dnf copr enable OWNER/halcyon fedora-44
   Then install, e.g.: sudo dnf install hyprland"

   # build-time repos: Terra 44 (buildroot macros) + lionheartp/Hyprland
   # (lowest-priority bootstrap only)
   copr-cli edit-chroot halcyon/fedora-44-x86_64 --repos \
     "https://repos.fyralabs.com/terra44 \
      https://download.copr.fedorainfracloud.org/results/lionheartp/Hyprland/fedora-44-x86_64/"
   ```

5. **Push the content**:

   ```bash
   git remote add origin git@github.com:OWNER/NAME.git
   git push -u origin main
   ```

   The push runs, unattended: the CI image build (builder-docker.yml), the
   validate job (which waits for the image), then the batch waves
   0 → 3 submitted to Copr — batch 4 is intentionally empty — and wave 5
   carrying the 40 texlive rolling groups. 52 of the packages get created
   server-side by their first build.
6. **Watch it land**:

   ```bash
   gh run watch             # or the Actions page
   copr-cli monitor halcyon # per-package Copr states
   ```

7. **Consumers**:

   ```bash
   dnf copr enable OWNER/halcyon fedora-44
   # or, to make everything here shadow Fedora/Terra:
   sudo cp repo/halcyon.repo /etc/yum.repos.d/   # priority=1 + project GPG key
   sudo dnf install hyprland texlive-meta        # texlive-meta = the whole scheme, no docs
   ```

8. **Re-enable the automation** — install the
   [Renovate GitHub App](https://github.com/apps/renovate) once (the
   checked-in `renovate.json` drives it); `update.yml` (sweep, Mondays
   04:17 UTC), `texlive-update.yml` (biweekly Wednesday roll) and
   `repoclosure.yml` (post-cascade + daily) run on their own.

Two upstream constraints Copr enforces: builds are pruned (the newest build
per package is kept, older ones expire after 14 days), and package content
must use Fedora-allowed licenses.
