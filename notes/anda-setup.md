# anda-setup.md — putting halcyon-packages on anda

This restores the anda/GitHub-Pages flow (`autobuild.yml` + a publish step,
GPG signing + createrepo_c + the `GPG_PRIVATE_KEY` secret) in terra's current
shape: `anda build` runs in mock chroots inside a builder container on GitHub
Actions, and `ci/publish.sh` signs, indexes and deploys the dnf repo to the
gh-pages branch. The builds need no Copr project, no copr-cli and no FAS
account — the builder image and the Actions run are the whole build farm.

Order matters: the builder image and the signing key must exist before the
first wave run; nothing else needs external setup.

## Stage 1 — the builder image

`builder-docker.yml` builds `ghcr.io/<owner>/halcyon-builder:f44` from
`.github/builder/Dockerfile` (push to main touching `.github/builder/**` or
`mock/**`, or run it manually). The image carries: anda + anda-srpm-macros
(from the public Terra repos), mock + mock-scm, rpm-build/rpmdevtools,
rpm-sign + gnupg2 (publish), createrepo_c, jq/gh/curl, and the halcyon mock
config at `/etc/mock/halcyon-f44-x86_64.cfg`.

Wait for the image job to go green before the first build run — the build
jobs pull the image by that name.

Local builds use the same image (see *Day-to-day*).

## Stage 2 — the RPM signing key

The Pages repo is signed by your own key. Generate one if you do not have one
from the previous anda era:

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

Then on GitHub (Settings → Secrets and variables → Actions):

| secret | value |
| --- | --- |
| `GPG_PRIVATE_KEY` | the armored secret key (the whole `-----BEGIN ... KEY BLOCK-----`) |
| `GPG_PASSPHRASE` | the key's passphrase; omit/empty for a passphrase-less key |

`ci/publish.sh` imports the key (ghaction-import-gpg), signs every RPM of the
wave with `rpmsign`, and exports the public key to
`repo/RPM-GPG-KEY-halcyon-packages` on Pages — that is the key
`repo/halcyon-packages.repo` points its `gpgkey` at.

## Stage 3 — repository settings on GitHub

- **Pages**: Settings → Pages → Source: *Deploy from a branch*, branch
  `gh-pages`, path `/(root)` — but leave it unconfigured until the first
  publish: `ci/publish.sh` seeds the `gh-pages` branch itself and the push
  makes the site appear.
- No other secrets. (The Copr-era `COPR_CLICONF` secret and the
  `COPR_PROJECT`/`COPR_CHROOT` variables are obsolete — delete them.)

## Stage 4 — first run

Run `.github/workflows/anda-build.yml` (Run workflow, empty `only`):

```text
validate → manifest (ci/matrix.py splits the build matrix into batch waves)
build0   (29 packages, in parallel)  → publish0  (sign + createrepo + Pages)
build1   (8 packages)                → publish1
build2   (hyprland, ~15 min)     → publish2
```

Each wave publishes before the next builds — that publish is what makes the
lower batch's RPMs installable BuildRequires of the next wave (the buildroot
carries the Pages repo via the mock config). On pull requests the publish
jobs skip signing/pushing and only validate.

Then verify from a client:

```bash
# the Pages repo (repo/halcyon-packages.repo mirrors it)
curl -fsSL https://aahsnr-work.github.io/halcyon-packages/repo/f44/halcyon-packages.repo
# the signing key
curl -fsSL https://aahsnr-work.github.io/halcyon-packages/repo/RPM-GPG-KEY-halcyon-packages | gpg --show-keys

sudo dnf install hyprland   # pulls the whole batch 0→1→2 chain
```

## Stage 5 — the daily sweep

`anda-update.yml` runs `anda update` daily at 04:17 UTC: every package's
`update.rhai` queries its upstream feed and edits its spec in place. The
workflow commits the sweep to a `bump/<YYYYMMDD>` branch and opens one PR;
merging it triggers `anda-build.yml` for the changed packages plus every
higher batch. Dispatch it manually the first time and review the produced PR
(the 40 rhai ports of the old fetch.sh sweepers are new).

## Day-to-day

| what | how |
| --- | --- |
| build after a merge | automatic — `anda-build.yml` (push to `main`) |
| rebuild everything | Actions → anda-build → Run workflow (empty `only`) |
| rebuild one package | Actions → anda-build → Run workflow, `only = <pkg>` (its higher batches rebuild too) |
| upstream version bumps | automatic — `anda-update.yml` opens one PR/day; review & merge |
| manual sweep check | `anda update` locally (needs `GITHUB_TOKEN=$(gh auth token)` to avoid API rate limits) |
| local package build | `podman run --rm -it --privileged -v "$PWD":/h -w /h ghcr.io/<owner>/halcyon-builder:f44 anda build <pkg> -c halcyon-f44-x86_64` |
| watch status | the Actions run page — wave jobs name their package in the title |
| publish manually | `GPG_KEY_ID=<fpr> ci/publish.sh rpms srpms` from a run's artifacts |

## What changed relative to the Copr setup (migration notes)

- `copr.d/<pkg>/` → `anda/<pkg>/` (flat; the old layout was
  `anda/<category>/<pkg>/` — categories dropped, `strip_prefix = "anda/"` in
  the root anda.hcl does the naming).
- `copr/packages.toml` (`script` + `batch`) → `ci/packages.toml` (`batch`
  only; the manifest lives in each `anda.hcl`).
- `copr/submit.py --since` (changed pkgs + higher batches) → `ci/matrix.py
  --since` — same cascade semantics, emitting terra's `build_matrix=`
  JSON shape; batch waves are enforced by the workflow's `needs` chain.
- `copr/submit.py` payload rendering + `copr/lib.sh` → gone: specs carry full
  `Source*` URLs that mock downloads at SRPM-build time (anda defines
  `_disable_source_fetch 0`); repo files (metainfo, patches, helpers) sit in
  the package directory.
- `copr/sync.py` + `copr/lib-bump.sh` + `copr.d/*/fetch.sh` → `anda update`
  driving `anda/<pkg>/update.rhai` (the 40 sweepers ported to rhai; the
  snapshot-counter logic of hyprland/noctalia kept, the version-compare
  now via `rpmdev-vercmp` through andax's `sh()`).
- `copr/watch.py` → the Actions run UI (wave jobs name their package).
- `copr/project-setup.sh` (Copr project) → gone; `copr/test-source.sh` →
  superseded by `anda build` itself (the mock backend covers the source step
  and the full RPM build).
- Signing: Copr's project key → `ci/publish.sh` + the `GPG_PRIVATE_KEY`
  secret (the old hand-rolled key returns; `rpmsign`, `createrepo_c` and the
  Pages deployment are back, scripted in CI).
- `%autorelease`/`%autochangelog` → explicit `Release: N%{?dist}` + a written
  changelog (terra's spec convention; Copr's hand-rolled expansion in
  `copr/lib.sh` is gone). `anda-srpm-macros` stays in the buildroot for the
  terra macros some specs already carry.
