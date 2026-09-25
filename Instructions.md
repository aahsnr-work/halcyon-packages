# halcyon-packages — A-to-Z setup guide

This document is the complete recipe for recreating **halcyon-packages** from
zero: a self-published **anda** monorepo that builds, signs and serves every
non-Fedora RPM the halcyon image consumes, with automated upstream version
tracking — from an empty directory to `dnf install` working on a client
machine.

| stage | what you end up with                                                  |
| ----- | --------------------------------------------------------------------- |
| 1     | local tooling ready                                                   |
| 2     | this code pushed to a **public** GitHub repository `halcyon-packages` |
| 3     | the builder image `ghcr.io/<owner>/halcyon-builder:f44`               |
| 4     | a GPG signing key wired up (`GPG_PRIVATE_KEY` secret)                 |
| 5     | all packages built in 3 batch waves, published on GitHub Pages        |
| 6     | the repo enabled on any Fedora 44 machine                             |

Related documents: `README.md` (layout + how a build works), `TODO.md`
(status), `notes/anda-setup.md` (migration notes + day-to-day).

---

## 1. Prerequisites

| requirement               | why                                                                      | check                         |
| ------------------------- | ------------------------------------------------------------------------ | ----------------------------- |
| A **GitHub account**      | hosts the repo, runs the four workflows, receives the Pages site         | —                             |
| `git`                     | versioning; the CI pins nothing but the wave history matters             | `git --version`               |
| `python3 ≥ 3.11`          | `ci/matrix.py` (stdlib only, incl. `tomllib`)                            | `python3 -c 'import tomllib'` |
| `podman` **or** `docker`  | local builds + the builder image                                         | `podman --version`            |
| `gh` (optional)           | PR creation for the bump flow is CI-side; locally useful for auth tokens | `gh --version`                |
| A GPG key for RPM signing | the Pages repo is signed by your own key (stage 4)                       | `gpg --list-keys`             |

Everything in `ci/` is stdlib Python + POSIX/bash shell; the heavy lifting
(`anda`, `mock`, `rpmsign`, `createrepo_c`, `rpmdevtools`) lives in the
builder image, not on the host.

---

## 2. Create the GitHub repository and push the code

> **The repository must be PUBLIC.** The published dnf repo is served from
> GitHub Pages (public by definition), the builder image is pulled by the
> Actions build jobs, and `anda update`'s rhai helpers talk to the public
> GitHub API. There is no secret in the repo that forbids publishing (the
> signing key lives only in GitHub Actions secrets).

```bash
cd ~/Git/work
# the tree is already a git repository with the migration committed; if
# starting from a bare copy:
#   git init -b main && git add -A && git commit -m "halcyon-packages: initial commit"

# create the empty repo on GitHub (no README/license — the tree already has one)
gh repo create halcyon-packages --public --source . --push
# … or manually:
#   git remote add origin git@github.com:<owner>/halcyon-packages.git
#   git push -u origin main
```

Verify the default branch is `main` (the workflows trigger on `main`):
`gh repo view --json defaultBranchRef`.

### What gets pushed

| path                                   | role                                                                                          |
| -------------------------------------- | --------------------------------------------------------------------------------------------- |
| `anda.hcl`                             | root manifest — `strip_prefix = "anda/"`                                                      |
| `anda/<pkg>/`                          | one directory per package: `<pkg>.spec`, `anda.hcl`, `update.rhai`, files the spec references |
| `ci/packages.toml`                     | the registry — a package without an entry here is never built                                 |
| `ci/matrix.py`                         | the build-matrix generator (changed packages + higher batches, per batch)                     |
| `ci/publish.sh`                        | sign + createrepo_c + prune + gh-pages deploy                                                 |
| `mock/halcyon-f44-x86_64.cfg`          | the buildroot definition (shipped in the builder image)                                       |
| `.github/builder/Dockerfile`           | the builder image (mock, anda, signing tooling)                                               |
| `.github/workflows/anda-build.yml`     | validate + wave builds + publish on push/PR/manual                                            |
| `.github/workflows/anda-publish.yml`   | the reusable per-wave publish job                                                             |
| `.github/workflows/anda-update.yml`    | daily version sweep → one bump PR                                                             |
| `.github/workflows/builder-docker.yml` | builds/pushes the builder image                                                               |
| `repo/halcyon-packages.repo`           | client-side dnf repo file (Pages URL, `priority=1`)                                           |

---

## 3. Build the builder image

`.github/workflows/builder-docker.yml` builds and pushes the image on the
first push touching `.github/builder/**` or `mock/**` (or run it manually
from the Actions tab). Nothing to configure — it uses the stock
`GITHUB_TOKEN` with packages:write.

The image is `registry.fedoraproject.org/fedora-minimal:44` plus:

- `anda` + `anda-srpm-macros` — installed from the **public Terra repos**
  (they are not packaged in Fedora; the Dockerfile enables terra44
  temporarily for that transaction, same as terrapkg/builder itself),
- `mock`, `mock-scm`, `rpm-build`, `rpmdevtools`, `createrepo_c`,
  `rpm-sign`, `gnupg2`, `jq`, `gh`, `curl`, `mold`,
- the halcyon mock config at `/etc/mock/halcyon-f44-x86_64.cfg`.

Wait for the image job to go green before the first build run — the wave
jobs pull `ghcr.io/<owner>/halcyon-builder:f44` by name.

---

## 4. Configure the signing key — secrets

The Pages repo is signed by your own GPG key (Cop signs nothing for you any
more). Generate one if you do not have one from the previous anda era:

```bash
gpg --batch --gen-key <<'EOF'
%no-protection
Key-Type: RSA
Key-Length: 3072
Name-Real: halcyon-packages
Name-Email: packages@halcyon.invalid
Expire-Date: 0
%commit
EOF
gpg --armor --export-secret-keys packages@halcyon.invalid
```

Repo → Settings → Secrets and variables → Actions:

| kind       | name              | value                                   | required                                                           |
| ---------- | ----------------- | --------------------------------------- | ------------------------------------------------------------------ |
| **Secret** | `GPG_PRIVATE_KEY` | the **entire armored secret key block** | **yes** — without it the publish jobs abort with an explicit error |
| Secret     | `GPG_PASSPHRASE`  | the key's passphrase                    | only if the key is passphrase-protected                            |

`ci/publish.sh` imports the key inside the builder container, signs every RPM
of the wave (`rpmsign`), and exports the public key to Pages at
`repo/RPM-GPG-KEY-halcyon-packages` — the key `repo/halcyon-packages.repo`
points its `gpgkey` at. If builds suddenly fail at signing, the secret or the
key likely changed — re-check `gpg --show-keys` against the Pages URL.

**If you are migrating from the Copr setup** (skip when creating fresh):
delete the `COPR_CLICONF` secret and the `COPR_PROJECT`/`COPR_CHROOT`
variables — they are obsolete. The old hand-rolled key from the
anda/GitHub-Pages era can come straight back if you still have its secret.

### The workflows

| workflow             | trigger                                                          | what it does                                                                                                                                                                                                                                                                                       |
| -------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `builder-docker.yml` | push touching `.github/builder/**`/`mock/**`, PRs, manual        | builds/pushes `ghcr.io/<owner>/halcyon-builder:f44`                                                                                                                                                                                                                                                |
| `anda-build.yml`     | push to `main` touching `anda/**`/`ci/**`/`mock/**`, PRs, manual | job 1 _validate_: shell/python syntax, registry consistency (every registered package has `anda.hcl`+spec+`update.rhai`, batches contiguous), the build plan; then _manifest_ (`ci/matrix.py` → per-batch matrices) and the wave chain `build0 → publish0 → build1 → publish1 → build2 → publish2` |
| `anda-publish.yml`   | workflow_call                                                    | one wave: download artifacts, `rpmsign` (secrets-imported key), `createrepo_c`, prune superseded versions, deploy gh-pages; PRs validate only                                                                                                                                                      |
| `anda-update.yml`    | daily 04:17 UTC + manual                                         | runs `anda update` (every package's `update.rhai`), pushes one `bump/<YYYYMMDD>` branch, opens one PR. **Merging the bump PR is what triggers builds** — `anda-build.yml` then builds the changed packages plus every higher batch                                                                 |
| `dependabot.yml`     | weekly Monday                                                    | groups all GitHub Actions bumps into one PR                                                                                                                                                                                                                                                        |

Push-event selection logic (in `ci/matrix.py --since <sha>`): every package
whose `anda/` directory changed, **plus every package in a higher batch** (a
changed lower batch may invalidate dependents). Touches under `ci/`,
`mock/`, `.github/builder/` or the root `anda.hcl` rebuild everything.

---

## 5. First run

Do it once manually from Actions → anda-build → Run workflow with an empty
`only` (or locally, wave by wave — see the troubleshooting note):

```bash
python3 ci/matrix.py --list        # print the resolved plan (40 pkgs, 3 batches)
gh workflow run anda-build.yml     # real: 3 sequential waves
```

Each build is `anda build <pkg> -c halcyon-f44-x86_64` (mock backend)
inside the builder container; each publish signs + indexes + deploys to
Pages. The wave chain (`needs`) guarantees the order; the Pages publish
between waves is what the lower batch's dependents install from.

Batch layout (must stay contiguous; packages inside one batch never depend on
each other):

- **batch 0** — 33 packages: the CLI-tool set (`atuin`, `bat`, `cava`,
  `chafa`, `dust`, `eza`, `gnuplot`, `lazygit`, `pandoc`, `pixi`,
  `starship`, `tealdeer`, `uv`, `yazi`, `zellij`), vendor apps
  (`bitwarden`, `bun`, `distroshelf`, `nwg-look`, `obsidian`, `opencode`,
  `qt6ct`, `ticktick`, `xwiimote-ng`, `zotero`) and the
  Hyprland/noctalia roots (`hyprland-protocols`, `hyprlang`, `hyprutils`,
  `hyprwayland-scanner`, `noctalia-git`, `noctalia-greeter-git`, `pyprland`)
- **batch 1** — 8 packages: `aquamarine`, `hyprcursor`, `hyprgraphics`,
  `hyprland-guiutils`, `hyprland-qt-support`, `hyprpwcenter`,
  `hyprshutdown`, `xdg-desktop-portal-hyprland` — link against batch 0
- **batch 2** — 1 package: `hyprland-git` (~15 min) — links against
  batches 0+1

Watch the Actions run: the wave jobs name their package in the job title.

`xwiimote-ng` has never been built anywhere (anda era included) — treat its
first anda build as its validation. Everything else built under both the old
anda system and Copr.

---

## 6. Verify the repository from a client

```bash
# the published repo (repo/halcyon-packages.repo in this repo mirrors it)
curl -fsSL https://aahsnr-work.github.io/halcyon-packages/repo/f44/halcyon-packages.repo

# the signing key
curl -fsSL https://aahsnr-work.github.io/halcyon-packages/repo/RPM-GPG-KEY-halcyon-packages | gpg --show-keys

sudo curl -fsSL https://aahsnr-work.github.io/halcyon-packages/repo/f44/halcyon-packages.repo \
    -o /etc/yum.repos.d/halcyon-packages.repo
sudo dnf install hyprland-git   # pulls the whole batch 0→1→2 dependency chain
```

`repo/halcyon-packages.repo` hard-codes the `aahsnr-work` Pages URL; if your
owner differs, regenerate it from `templates/halcyon-packages.repo.tmpl`.

**Important — the repo file sets `priority=1`**, so dnf always installs these
packages from halcyon-packages even when Fedora or Terra carry the same name
(repo priority wins over version). There is no `dnf copr enable` equivalent —
installing the repo file is the only client-side step.

The 14 CLI tools the halcyon image requires from this repo specifically:
`atuin`, `bat`, `bun`, `cava`, `chafa`, `dust`, `eza`, `gnuplot`, `pixi`,
`starship`, `tealdeer`, `uv`, `yazi`, `zellij`.

**Runtime note:** `hyprland-guiutils`, `hyprpwcenter` and `hyprshutdown` link
against `libhyprtoolkit`, which this repo does not package yet — the image must
also enable `lionheartp/Hyprland` until `hyprtoolkit`/`hyprwire`/`glaze` are
packaged here (see TODO.md).

---

## 7. Day-to-day

| what                     | how                                                                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| build after a merge      | automatic — `anda-build.yml` builds changed packages + higher batches                                                                 |
| rebuild everything       | Actions → anda-build → Run workflow, leave `only` empty                                                                               |
| rebuild one package      | Actions → anda-build → Run workflow, `only = <pkg>` (also builds its higher batches)                                                  |
| upstream version bumps   | automatic — `anda-update.yml` opens one PR/day; review & merge                                                                        |
| manual version check     | `GITHUB_TOKEN=$(gh auth token) anda update` locally                                                                                   |
| local package build      | `podman run --rm -it --privileged -v "$PWD":/h -w /h ghcr.io/<owner>/halcyon-builder:f44 anda build <pkg> -c halcyon-f44-x86_64` |
| manual publish of a wave | download the run's artifacts and `GPG_KEY_ID=<fpr> ci/publish.sh rpms srpms`                                                          |
| change the buildroot     | edit `mock/halcyon-f44-x86_64.cfg`; `builder-docker.yml` rebuilds the image                                                           |

### Adding a new package from scratch

1. `mkdir anda/<pkg>`; write `<pkg>.spec` from `templates/source-build.spec.tmpl`
   (builds from upstream source) or `templates/binary-wrapper.spec.tmpl`
   (repackages an upstream release binary). Constraints that bite:
   - full URLs in `Source*` (mock fetches them at SRPM-build time); no
     downloads in `%prep` — read files from `%{_sourcedir}` or
     `%setup -a 0`;
   - explicit `Release: N%{?dist}` + a written `%changelog` (no rpmautospec);
   - extra build-time repos go in `anda.hcl`'s `rpm.extra_repos` (double
     backslashes escape rpm variables: `\\$releasever`).
2. Write `anda/<pkg>/anda.hcl` from `templates/anda.hcl.tmpl`.
3. Write `anda/<pkg>/update.rhai` from `templates/update.rhai.tmpl` so the
   daily sweep keeps it fresh.
4. Build locally (the command above) — the mock chroot covers the SRPM step
   and the full RPM build, so a green local build is a green CI build.
5. Register in `ci/packages.toml`:
   ```toml
   [<pkg>]
   batch = <max(batch of every build-dep) + 1>
   ```
6. Push — `anda-build.yml` builds it (or dispatch with `only = <pkg>`).

Batch rules recap: batch 0 may only use Fedora + `lionheartp/Hyprland`
(mock-config-level repos); same-batch packages build in parallel and must
never depend on each other; a package without a registry entry is never
built.

---

## 8. Package matrix

**Legend** — the 42 hand-maintained packages plus the 388 generated
  texlive packages (see TODO.md) are registered; the open items are the two
never-validated builds.

> Built status: **none yet** — the first anda run has not happened. After it,
> the Actions run page + `repo/f44/x86_64/repodata/` reflect the live status
> of exactly the 40 rows below.

### Registered — 42 packages in batches 0–2 + the grouped texlive-texmf (batch 3)

|   # | package                     | batch | version tracked      | type                                                              |
| --: | --------------------------- | ----- | -------------------- | ----------------------------------------------------------------- |
|   1 | atuin                       | 0     | 18.22.0              | wrapper (official gnu tarball)                                    |
|   2 | bat                         | 0     | 0.26.1               | wrapper (man + completions included)                              |
|   3 | bitwarden                   | 0     | 2026.9.0             | vendor-RPM rewrap (anudeepd spec; byte-identical payload)         |
|   4 | bun                         | 0     | 1.4.2                | wrapper (baseline release zip + shell completions, terrapkg spec) |
|   5 | cava                        | 0     | 1.0.0                | source build (autotools; ALSA/PipeWire/Pulse/JACK)                |
|   6 | chafa                       | 0     | 1.18.2               | source build (autotools, terrapkg spec)                           |
|   7 | distroshelf                 | 0     | 1.5.2                | source build (meson + cargo, upstream meson.build)                |
|   8 | dust                        | 0     | 1.2.6                | wrapper                                                           |
|   9 | eza                         | 0     | 0.23.5               | wrapper (man + completions included)                              |
|  10 | gnuplot                     | 0     | 6.0.5                | source build (SourceForge, lean cairo/console)                    |
|  11 | hyprland-protocols          | 0     | 0.7.1                | source build (hyprwm)                                             |
|  12 | hyprlang                    | 0     | 0.6.8                | source build (hyprwm)                                             |
|  13 | hyprutils                   | 0     | 0.14.2               | source build (hyprwm)                                             |
|  14 | hyprwayland-scanner         | 0     | 0.4.6                | source build (hyprwm)                                             |
|  15 | lazygit                     | 0     | 0.65.1               | wrapper                                                           |
|  16 | noctalia-git                | 0     | 5.1.0^18.git\<sha\>  | source build (main-branch pin)                                    |
|  17 | noctalia-greeter-git        | 0     | 1.5.0^8.git\<sha\>   | source build (main-branch pin)                                    |
|  18 | obsidian                    | 0     | 1.13.7               | wrapper (vendor tarball, Arch layout; digest verified in %prep)   |
|  19 | opencode                    | 0     | 2.0.14               | wrapper (npm release tarball; scope rewritten by update.rhai)     |
|  20 | pandoc                      | 0     | 3.11                 | wrapper                                                           |
|  21 | pixi                        | 0     | 0.81.0               | wrapper (official musl binary + completions)                      |
|  22 | pyprland                    | 0     | 3.4.4                | source build (hatchling wheel + C client, AUR PKGBUILD)           |
|  23 | starship                    | 0     | 1.26.0               | wrapper                                                           |
|  24 | tealdeer                    | 0     | 1.9.0                | wrapper (official musl binary + completions)                      |
|  25 | ticktick                    | 0     | 8.0.11               | wrapper (vendor .deb, AUR PKGBUILD)                               |
|  26 | uv                          | 0     | 0.12.17              | wrapper (official musl tarball, uv + uvx + completions)           |
|  27 | xwiimote-ng                 | 0     | 3.0.1                | source build — **never built anywhere**                           |
|  28 | yazi                        | 0     | 26.9.1               | wrapper                                                           |
|  29 | zellij                      | 0     | 0.45.1               | wrapper                                                           |
|  31 | zotero                      | 0     | 10.0.3               | wrapper — terrapkg's spec layout (npm source build dormant)       |
|  32 | aquamarine                  | 1     | 0.15.1               | source build (hyprwm)                                             |
|  33 | hyprcursor                  | 1     | 0.1.13               | source build (hyprwm)                                             |
|  34 | hyprgraphics                | 1     | 0.5.1                | source build (hyprwm)                                             |
|  35 | hyprland-guiutils           | 1     | 0.2.2                | source build (hyprwm)                                             |
|  36 | hyprland-qt-support         | 1     | 0.1.0                | source build (hyprwm)                                             |
|  37 | hyprpwcenter                | 1     | 0.1.2                | source build (hyprwm)                                             |
|  38 | hyprshutdown                | 1     | 0.1.1                | source build (hyprwm)                                             |
|  39 | xdg-desktop-portal-hyprland | 1     | 1.4.1                | source build (hyprwm)                                             |
|  40 | hyprland-git                | 2     | 0.56.2^58.git\<sha\> | source build (main-branch pin)                                    |

### Not packaged here on purpose (runtime gap)

| what                                           | where it comes from                          | why                                                                                                                                                                                                                                  |
| ---------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| hyprtoolkit, hyprwire, glaze(-static), wlroots | `lionheartp/Hyprland` COPR (build + runtime) | packaging them here is the main self-containment TODO — `hyprland-guiutils`/`hyprpwcenter`/`hyprshutdown` link `libhyprtoolkit` at runtime                                                                                           |
| bazaar                                         | COPR `ublue-os/packages`                     | user decision (2026-09-22): installed from ublue-os/packages, not built here (their f44 build is 0.9.3-4; recent builds failing)                                                                                                     |
| bazzite-portal                                 | Terra repo (`repos.fyralabs.com/terra44`)    | user decision (2026-09-22): installed from Terra, not built here                                                                                                                                                                     |
| TeX Live (Fedora's scheme packages)             | superseded for this image                    | this repo builds the Arch-style grouped `texlive-texmf` (scheme-full, no docs) and serves it from the R2 bucket — `tools/texlive-splitter/` regenerates it per snapshot |

---

## 9. Troubleshooting

| symptom                                                             | cause / fix                                                                                                                                                                              |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| publish job fails: `set the GPG_PRIVATE_KEY repository secret`      | the secret is missing/empty — stage 4                                                                                                                                                    |
| build jobs never start: manifest red                                | `ci/matrix.py` validation failed — check the manifest job log (registry consistency, batches)                                                                                            |
| `anda build` fails at the **SRPM step** with 404 on a `Source*` URL | the upstream artifact moved or the URL pattern drifted after a bump — check the release assets against the spec's `Source*` lines                                                        |
| build fails in mock with `File not found` in `%files`               | a `Source*`/`Patch*` the spec declares was never fetched, or a soname/%files path drifted after an upstream bump — reproduce with the local `anda build`                                 |
| wave N+1 fails resolving a build dependency                         | the previous wave's publish is missing (see the publish job log) or the dep is missing from the Pages repo entirely — check `repo/f44/x86_64/repodata/`                                  |
| client says the repo is unsigned                                    | compare the key at `repo/RPM-GPG-KEY-halcyon-packages` with `gpg --show-keys`; `repo/*.repo` points `gpgkey` at exactly that file                                                        |
| `anda update` fails with `env(GITHUB_TOKEN) not present`            | the andax `gh*` helpers need the token — dispatch via `anda-update.yml` (passes `github.token`) or export it locally                                                                     |
| a daily bump PR turns a build red                                   | the upstream artifact naming changed (wrapper packages) — check the release assets against the spec's URL pattern                                                                        |
| `matrix.py: cannot determine the revision`                          | run it from a git clone (it uses `git diff --name-only REV..HEAD`)                                                                                                                       |
| Pages site 404 right after the first run                            | the `gh-pages` branch exists but Pages is still deploying — give it a minute, check Settings → Pages                                                                                     |
| Pages repo stops serving new versions                               | the publish step prunes superseded versions; if `du -sh` (publish log) nears GitHub's Pages budget, old versions are kept by design — clear space by pruning in `ci/publish.sh`'s keep-N |

---

## 10. Quick reference — the pipeline in one picture

```
                 ci/packages.toml  (registry: batch per package)
                        │
   push to main ──► anda-build.yml ──► validate (sh/py/registry/plan)
                        │                    │
   PRs ────────────► validate only ────────┘
                        │
                        ▼
              ci/matrix.py --since <push-sha>
              changed pkgs + every higher batch, split into batch waves
                        │
                        ▼
   ┌──────────── wave 0 (matrix: 33 packages, parallel) ─────────────┐
   │ anda build <pkg> -c halcyon-f44-x86_64                     │
   │   container: ghcr.io/<owner>/halcyon-builder:f44 (privileged)   │
   │   mock --buildsrpm (URL sources fetched on the host)            │
   │   mock --rebuild in halcyon-f44-x86_64:                         │
   │     Fedora 44 + updates + Pages repo + lionheartp/Hyprland      │
   └────────────────────────────┬────────────────────────────────────┘
                        ▼  ci/publish.sh: rpmsign → createrepo_c →
                           prune superseded → deploy gh-pages
                        │
   ┌──────────── wave 1 (8 packages) ── wave 2 (hyprland-git) ───────┐
   │   (each wave's buildroot sees the previous wave's output        │
   │    through the Pages repo that publish just refreshed)          │
   └─────────────────────────────────────────────────────────────────┘
                        ▼
   https://aahsnr-work.github.io/halcyon-packages/repo/f44/  (+ GPG key)

   daily 04:17 UTC: anda-update.yml → anda update (update.rhai × 40)
     → bump/<date> branch → one PR → merge → anda-build.yml waves
```
