#!/bin/bash
# obs-local.sh — build halcyon-packages specs locally the way
# build.opensuse.org would: osc + obs-build inside podman, resolving the
# buildroot against the home:halcyon041/Fedora_44 build config fetched from
# the OBS API (same repos, same prjconf, same expansion as the backend).
#
# Usage:
#   tools/obs-local.sh [--faithful] [--] PKG [PKG...]
#
#   PKG          registry key(s) under anda/ (e.g. glaze hyprtoolkit)
#   --faithful   build with --vm-type=podman (obs-build's --net=none), which
#                reproduces the OBS workers' network isolation exactly —
#                including the failure of any build-time fetching (cargo
#                fetch, go proxy, …). Default is chroot (fast, no network
#                block).
#
# Environment:
#   OBS_LOCAL_IMAGE   image to use   (default localhost/obs-local:44; built
#                     on first use from tools/obs-local/Containerfile)
#   OBS_PROJECT       project to resolve against (default home:halcyon041)
#   OBS_LOCAL_EXTRA   extra args passed through to osc build (e.g. "-x gtest")
#
# Requires: podman; osc credentials in ~/.config/osc/oscrc (the file must
# carry user/pass — keyring-backed credentials are not visible in the
# container).
#
# Known limits (full notes in notes/obs-local-builds.md):
#   - the buildroot calculation happens SERVER-side: a BuildRequires only
#     satisfiable by a sibling package that has not been BUILT on OBS yet
#     fails with "unresolvable". Push first and let OBS bootstrap in
#     dependency order, or use the anda/mock flow for those packages.
#   - osc build has no extra-repo injection; use OBS_LOCAL_EXTRA="-x PKG"
#     or fall back to standalone `build --dist`.
set -euo pipefail

IMAGE=${OBS_LOCAL_IMAGE:-localhost/obs-local:44}
PROJECT=${OBS_PROJECT:-home:halcyon041}
REPO=Fedora_44
ARCH=x86_64

faithful=()
pkgs=()
while [ $# -gt 0 ]; do
	case "$1" in
	--faithful) faithful=(--vm-type=podman) ;;
	--) shift; break ;;
	-*) echo "obs-local.sh: unknown option $1" >&2; exit 2 ;;
	*) pkgs+=("$1") ;;
	esac
	shift
done
[ ${#pkgs[@]} -gt 0 ] || { echo "usage: tools/obs-local.sh [--faithful] PKG [PKG...]" >&2; exit 2; }

if ! podman image exists "$IMAGE"; then
	echo "== building $IMAGE from tools/obs-local/Containerfile"
	podman build -t "$IMAGE" - < "$(dirname "$0")/obs-local/Containerfile"
fi

# persistent osc home (package/buildroot caches survive runs); the repo rule
# about build state under /var/tmp/builds applies here too
mkdir -p /var/tmp/builds/obs-local

for pkg in "${pkgs[@]}"; do
	spec="anda/$pkg/$pkg.spec"
	[ -f "$spec" ] || { echo "obs-local.sh: $spec not found" >&2; exit 1; }
	echo "== obs-local $pkg (${faithful[*]:-chroot})"
	# shellcheck disable=SC2086
	podman run --rm --privileged \
		-v "$PWD":/h -w /h \
		-v "$HOME/.config/osc":/osc-cfg:ro \
		-v /var/tmp/builds/obs-local:/osc-home \
		-e HOME=/osc-home \
		"$IMAGE" bash -ec '
		mkdir -p "$HOME/.config"
		rm -rf "$HOME/.config/osc"
		cp -a /osc-cfg "$HOME/.config/osc"
		cd /h
		exec osc build --local-package --alternative-project='"$PROJECT"' \
			'"${faithful[*]}"' '"${OBS_LOCAL_EXTRA:-}"' \
			'"$REPO $ARCH"' '"$spec"'
	'
done
