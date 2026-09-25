#!/bin/bash
# obs-local.sh — build halcyon-packages specs locally the way
# build.opensuse.org would: osc + obs-build, resolving the buildroot against
# the home:halcyon041/Fedora_44 build config fetched from the OBS API (same
# repos, same prjconf, same server-side expansion as the backend).
#
# ISOLATION MODEL (read this first):
#   default      the build runs inside a disposable podman container on the
#                host (obs-build's --vm-type=podman, --net=none — which also
#                reproduces the OBS workers' network isolation exactly). No
#                root, no host-level mounts; obs-build only bind-mounts the
#                prepared buildroot INTO that container.
#   --container  instead run everything inside the privileged
#                localhost/obs-local:44 image (chroot inside a container;
#                the same envelope as the repo's anda/mock builds). Needs an
#                oscrc with a plain user/pass — keyring-backed credentials
#                do not cross the container boundary.
#   Host-level chroot builds are intentionally NOT supported: obs-build's
#   chroot mode prepares and mounts a buildroot directly on the host, which
#   this repo deliberately never does outside a container.
#
# Usage:
#   tools/obs-local.sh [--container] [--] PKG [PKG...]
#   PKG   registry key(s) under anda/ (e.g. glaze hyprtoolkit)
#
# Environment:
#   OBS_PROJECT       project to resolve against (default home:halcyon041)
#   OBS_LOCAL_IMAGE   bootstrap image (default localhost/obs-local:44)
#   OBS_LOCAL_EXTRA   extra args passed through to osc build
#                     (e.g. "-x gtest"; must not contain --vm-type)
#
# Host-native mode bootstraps itself once: if no obs-build engine is
# installed, the arch-independent scripts are extracted from the
# localhost/obs-local:44 image into ~/.local (a wrapper pins BUILD_DIR) and
# osc's build-cmd is pointed at it. Removal:
#   rm -rf ~/.local/lib/build ~/.local/bin/build
#   osc config general build-cmd --delete
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

container=0
pkgs=()
while [ $# -gt 0 ]; do
	case "$1" in
	--container) container=1 ;;
	--) shift; break ;;
	-*) echo "obs-local.sh: unknown option $1" >&2; exit 2 ;;
	*) pkgs+=("$1") ;;
	esac
	shift
done
[ ${#pkgs[@]} -gt 0 ] || { echo "usage: tools/obs-local.sh [--container] PKG [PKG...]" >&2; exit 2; }
case "${OBS_LOCAL_EXTRA:-}" in
*--vm-type*) echo "obs-local.sh: OBS_LOCAL_EXTRA must not override --vm-type" >&2; exit 2 ;;
esac

for pkg in "${pkgs[@]}"; do
	[ -f "anda/$pkg/$pkg.spec" ] || { echo "obs-local.sh: anda/$pkg/$pkg.spec not found" >&2; exit 1; }
done

ensure_image() {
	if ! podman image exists "$IMAGE"; then
		echo "== building $IMAGE from tools/obs-local/Containerfile"
		podman build -t "$IMAGE" - < "$(dirname "$0")/obs-local/Containerfile"
	fi
}

if [ "$container" = 0 ]; then
	# host-native: make sure an obs-build engine exists and osc knows it.
	build_cmd=$(osc config build-cmd 2>/dev/null || true)
	if [ -z "$build_cmd" ] && command -v build >/dev/null 2>&1; then
		build_cmd=$(command -v build)
	fi
	if ! { [ -n "$build_cmd" ] && [ -x "$build_cmd" ]; } && ! [ -x /usr/bin/build ]; then
		echo "== bootstrapping obs-build into ~/.local (from $IMAGE)"
		ensure_image
		mkdir -p "$HOME/.local/bin" "$HOME/.local/lib"
		podman run --rm "$IMAGE" tar -C /usr -cf - lib/build bin/buildvc bin/unrpm \
			| tar -C "$HOME/.local" -xf -
		{ printf '#!/bin/bash\nexport BUILD_DIR="$HOME/.local/lib/build"\n'
		  printf 'exec "$HOME/.local/lib/build/build" "$@"\n'; } > "$HOME/.local/bin/build"
		chmod +x "$HOME/.local/bin/build"
		osc config general build-cmd "$HOME/.local/bin/build" >/dev/null
	fi
	# --vm-type=podman is mandatory here: never host-level chroot.
	for pkg in "${pkgs[@]}"; do
		echo "== obs-local $pkg (podman VM, host-native)"
		# shellcheck disable=SC2086
		osc build --local-package --alternative-project="$PROJECT" --no-verify \
			--vm-type=podman ${OBS_LOCAL_EXTRA:-} \
			"$REPO" "$ARCH" "anda/$pkg/$pkg.spec"
	done
	exit 0
fi

# container mode: chroot inside the privileged image (same envelope as the
# repo's anda/mock builds)
ensure_image
mkdir -p /var/tmp/builds/obs-local
for pkg in "${pkgs[@]}"; do
	echo "== obs-local $pkg (chroot inside $IMAGE)"
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
		exec osc build --local-package --alternative-project='"$PROJECT"' --no-verify \
			'"${OBS_LOCAL_EXTRA:-}"' \
			'"$REPO $ARCH"' '"anda/$pkg/$pkg.spec"'
	'
done
