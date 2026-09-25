#!/bin/bash
# ci/publish-r2.sh — publish the texlive-texmf RPMs to the Cloudflare R2
# bucket.
#
# The texlive-texmf set (one spec, all collection groups, multi-GB for
# scheme-full) cannot ride the ~1 GB GitHub Pages repo; it gets its own
# repository at the R2 baseurl instead. Same publish semantics as the Pages
# flow (sign → createrepo_c → prune superseded → deploy), minus git: R2 is a
# mutable store, so rclone sync replaces the whole set atomically (one
# snapshot for all groups).
#
# Bucket layout (must mirror the Pages repo's shape):
#
#   texlive/f44/x86_64/*.rpm   binary packages (with repodata)
#   texlive/f44/source/*.rpm   source packages (with repodata)
#   texlive/RPM-GPG-KEY-halcyon-packages   public signing key
#
# The client repo file's [halcyon-texlive] section points its baseurl at
# R2_PUBLIC_BASE + /texlive/f44/x86_64 and its gpgkey at the Pages-served
# key URL (the key is canonical there — this script re-exports it to the
# bucket too, for self-containment).
#
# Required environment:
#   GPG_KEY_ID        fingerprint of the imported signing key
#   GPG_PASSPHRASE    key passphrase; empty is fine for passphrase-less keys
#   R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY / R2_ENDPOINT   S3 credentials
#   R2_BUCKET         bucket name (default halcyon-packages)
#   R2_LOCAL_HOST     public baseurl WITHOUT scheme, e.g. rpm.<your-domain>
# Usage (from the repository root):
#   ci/publish-r2.sh <rpm-result-dir> <srpm-result-dir>
set -euo pipefail

RPMDIR="${1:?usage: ci/publish-r2.sh <rpm-result-dir> <srpm-result-dir>}"
SRPMDIR="${2:?usage: ci/publish-r2.sh <rpm-result-dir> <srpm-result-dir>}"
: "${GPG_KEY_ID:?publish-r2.sh: set GPG_KEY_ID (ghaction-import-gpg outputs.fingerprint)}"
: "${R2_ACCESS_KEY_ID:?publish-r2.sh: set R2_ACCESS_KEY_ID}"
: "${R2_SECRET_ACCESS_KEY:?publish-r2.sh: set R2_SECRET_ACCESS_KEY}"
: "${R2_ENDPOINT:?publish-r2.sh: set R2_ENDPOINT (https://<account>.r2.cloudflarestorage.com)}"
R2_BUCKET="${R2_BUCKET:-halcyon-packages}"
R2_LOCAL_HOST="${R2_LOCAL_HOST:?publish-r2.sh: set R2_LOCAL_HOST (public domain, no scheme)}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-aahsnr-work/halcyon-packages}"

PREFIX="texlive/f44"
WORK="$GITHUB_WORKSPACE/r2-staging"

# --- 1. sign everything (same key as the Pages repo) --------------------------
export GNUPGHOME="${GNUPGHOME:-$HOME/.gnupg}"
sign_args=(--define "_gpg_name $GPG_KEY_ID")
if [ -n "${GPG_PASSPHRASE:-}" ]; then
    sign_args+=(
        --define "_gpg_sign_cmd_extra_args --batch --pinentry-mode loopback --passphrase $GPG_PASSPHRASE"
    )
fi
find "$RPMDIR" "$SRPMDIR" -name '*.rpm' -type f -print0 |
    xargs -0 -n1 rpmsign "${sign_args[@]}" --addsign
echo "publish-r2: signed $(find "$RPMDIR" "$SRPMDIR" -name '*.rpm' | wc -l) packages"

# --- 2. prune superseded versions of the same package -------------------------
# NOTE: full-snapshot semantics — every build produces the COMPLETE set (one
# spec, all groups, one snapshot), and step 4's `rclone sync --checksum`
# replaces the tree wholesale, deleting whatever this snapshot no longer
# contains. Per-file pruning logic (ci/publish.sh) would only matter for
# partial publishes.

# --- 3. stage the tree (bucket layout mirrors the Pages repo) ------------------
STAGE="$GITHUB_WORKSPACE/r2-stage"
rm -rf "$STAGE"
mkdir -p "$STAGE/$PREFIX/x86_64" "$STAGE/$PREFIX/source"
mv -v "$RPMDIR"/*.rpm "$STAGE/$PREFIX/x86_64/"
mv -v "$SRPMDIR"/*.src.rpm "$STAGE/$PREFIX/source/" 2>/dev/null || true

createrepo_c --quiet "$STAGE/$PREFIX/x86_64"
createrepo_c --quiet "$STAGE/$PREFIX/source"
# repo_gpgcheck=1 in the repo files — dnf5 drops unsigned metadata
# nondeterministically, so sign it with the same key as the packages
for store in "$STAGE/$PREFIX/x86_64" "$STAGE/$PREFIX/source"; do
    gpg --batch --yes --detach-sign --armor --local-user "$GPG_KEY_ID" \
        "$store/repodata/repomd.xml"
done
gpg --armor --export "$GPG_KEY_ID" > "$STAGE/$PREFIX/RPM-GPG-KEY-halcyon-packages"
du -sh "$STAGE"

# --- 4. rclone sync to the bucket ---------------------------------------------
# credentials via env (rclone reads them for the :s3 backend)
export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY"
export RCLONE_CONFIG_R2_ENDPOINT="$R2_ENDPOINT"
export RCLONE_CONFIG_R2_REGION="auto"
rclone sync "$STAGE/" "R2:$R2_BUCKET/" --checksum
rclone size "R2:$R2_BUCKET"

echo "publish-r2: done — baseurl https://$R2_LOCAL_HOST/$PREFIX/x86_64/"
