#!/bin/bash
# ci/publish.sh — publish built RPMs to the GitHub Pages dnf repository.
#
# The Copr pipeline delegated signing, repodata and repo serving to Copr; this
# script takes those jobs back, running per batch wave inside the builder
# container (which carries rpm-sign, gnupg2, createrepo_c and git).
#
# Layout on the gh-pages branch:
#
#   repo/f44/x86_64/*.rpm                 binary packages (with repodata)
#   repo/f44/source/*.rpm                 source packages (with repodata)
#   repo/RPM-GPG-KEY-halcyon-packages     public signing key
#
# Pruning: when a package's RPM is replaced by a newer version/release the
# superseded file is removed — old RPMs are the reason Pages has a size budget
# and the repo file sets priority=1 (version tiebreak is repo priority, not
# time). Pruning looks at the whole store (this wave + what is already on
# Pages) so a partial wave publish cannot resurrect an old version.
#
# Usage (from the repository root):
#   ci/publish.sh <rpm-result-dir> <srpm-result-dir>
#
# Required environment:
#   GPG_KEY_ID        fingerprint of the imported signing key (ghaction-import-gpg)
#   GPG_PASSPHRASE    key passphrase; empty is fine for passphrase-less keys
#   GITHUB_TOKEN      repo token used to push gh-pages
#   GITHUB_REPOSITORY owner/repo
set -euo pipefail

RPMDIR="${1:?usage: ci/publish.sh <rpm-result-dir> <srpm-result-dir>}"
SRPMDIR="${2:?usage: ci/publish.sh <rpm-result-dir> <srpm-result-dir>}"
: "${GPG_KEY_ID:?publish.sh: set GPG_KEY_ID (ghaction-import-gpg outputs.fingerprint)}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be set}"

PAGES="$GITHUB_WORKSPACE/pages"
KEYFILE="repo/RPM-GPG-KEY-halcyon-packages"
PREFIX="repo/f44"

# --- 1. check out the existing gh-pages (or seed an orphan branch) -----------
git config --global --add safe.directory "$GITHUB_WORKSPACE" || true
git fetch origin gh-pages --depth=1 2>/dev/null || true
git worktree remove -f pages 2>/dev/null || true
if git cat-file -e "origin/gh-pages^{tree}" 2>/dev/null; then
    git worktree add pages origin/gh-pages
else
    echo "publish: no gh-pages yet — seeding one"
    git worktree add --orphan pages
    (cd pages && git rm -rqf . 2>/dev/null || true)
fi

# --- 1b. Git LFS for the RPM store --------------------------------------------
# Several packages exceed GitHub's 100 MB per-file git limit (zotero, obsidian,
# bitwarden, ticktick, ...) — the store tracks all RPMs in LFS so the push is
# never rejected. Needs git-lfs in the builder image; the quota (free tier:
# 1 GB storage + 1 GB/month bandwidth) is the store's real budget — see the
# README's from-scratch recipe.
git lfs install
(
    cd pages
    git lfs track 'repo/f44/x86_64/*.rpm' 'repo/f44/source/*.rpm'
)

# --- 2. sign everything this wave produced -----------------------------------
export GNUPGHOME="${GNUPGHOME:-$HOME/.gnupg}"
sign_args=(--define "_gpg_name $GPG_KEY_ID")
if [ -n "${GPG_PASSPHRASE:-}" ]; then
    sign_args+=(
        --define "_gpg_sign_cmd_extra_args --batch --pinentry-mode loopback --passphrase $GPG_PASSPHRASE"
    )
fi
find "$RPMDIR" "$SRPMDIR" -name '*.rpm' -type f -print0 |
    xargs -0 -n1 rpmsign "${sign_args[@]}" --addsign
echo "publish: signed $(find "$RPMDIR" "$SRPMDIR" -name '*.rpm' | wc -l) packages"

# --- 3. prune superseded versions of the same package ------------------------
python3 - "$RPMDIR" "$SRPMDIR" "$PAGES/$PREFIX" <<'PY'
import glob, os, subprocess, sys

rpmdir, srpmdir, store = sys.argv[1:4]
files = sorted(glob.glob(os.path.join(store, "x86_64", "*.rpm")))
for d in (rpmdir, srpmdir):
    files += sorted(glob.glob(os.path.join(d, "*.rpm")))

def tag(path):
    q = subprocess.run(
        ["rpm", "-qp", "--qf", "%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}", path],
        capture_output=True, text=True, check=True,
    ).stdout
    name, version, release, arch = q.split("|")
    return name, version, release, arch != "src"

def vercmp(a, b):
    # rpmdev-vercmp exits 0 (equal), 11 (first newer) or 12 (second newer).
    rc = subprocess.run(["rpmdev-vercmp", a, b], capture_output=True).returncode
    return {11: 1, 12: -1}.get(rc, 0)

victims = set()
groups = {}
for path in files:
    name, version, release, is_binary = tag(path)
    groups.setdefault((name, is_binary), []).append((version, release, path))
for group in groups.values():
    for ver, rel, path in group:
        for over_ver, over_rel, over_path in group:
            if over_path == path:
                continue
            v = vercmp(over_ver, ver)
            if v > 0 or (v == 0 and vercmp(over_rel, rel) > 0):
                victims.add(path)
                break
for path in victims:
    os.unlink(path)
print(f"pruned {len(victims)} superseded package(s):")
for path in sorted(victims):
    print(f"  - {os.path.basename(path)}")
PY

# --- 4. move the survivors into the Pages store ------------------------------
mkdir -p "$PAGES/$PREFIX/x86_64" "$PAGES/$PREFIX/source"
if [ -n "$(find "$RPMDIR" -name '*.rpm' -print -quit)" ]; then
    mv -v "$RPMDIR"/*.rpm "$PAGES/$PREFIX/x86_64/"
fi
if [ -n "$(find "$SRPMDIR" -name '*.rpm' -print -quit)" ]; then
    mv -v "$SRPMDIR"/*.src.rpm "$PAGES/$PREFIX/source/"
fi

# --- 5. repodata + the public key --------------------------------------------
createrepo_c --quiet --update "$PAGES/$PREFIX/x86_64"
createrepo_c --quiet --update "$PAGES/$PREFIX/source"
# the repo files declare repo_gpgcheck=1 and dnf5 drops unsigned metadata
# nondeterministically (observed: in one wave, one chroot installed our
# hyprutils while another silently fell back to Fedora's stale package).
# Sign the repodata with the same key as the packages.
for store in "$PAGES/$PREFIX/x86_64" "$PAGES/$PREFIX/source"; do
    gpg --batch --yes --detach-sign --armor --local-user "$GPG_KEY_ID" \
        "$store/repodata/repomd.xml"
done
gpg --armor --export "$GPG_KEY_ID" > "$PAGES/$KEYFILE"
du -sh "$PAGES"

# --- 6. deploy ---------------------------------------------------------------
cd "$PAGES"
# -A (not -A repo): the .gitattributes that git lfs track wrote must be
# committed too, or the LFS patterns are lost on the next clone
git add -A
if [ -z "$(git status --porcelain)" ]; then
    echo "publish: nothing changed"
    exit 0
fi
git -c user.name="halcyon-ci" -c user.email="actions@users.noreply.github.com" \
    commit -m "publish: wave from run ${GITHUB_RUN_ID:-local}"
if [ -n "${GITHUB_TOKEN:-}" ]; then
    git push "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" \
        HEAD:gh-pages
else
    git push origin HEAD:gh-pages
fi
