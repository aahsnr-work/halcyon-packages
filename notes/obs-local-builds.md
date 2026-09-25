# Local OBS-equivalent builds (tools/obs-local.sh)

Build a halcyon-packages spec locally the way build.opensuse.org would:
same build config, same repo set (Fedora:44 + the project's own packages),
same dependency expansion — via `osc build` + obs-build inside podman.

```bash
tools/obs-local.sh glaze                 # podman VM (default, --net=none)
tools/obs-local.sh --container glaze     # chroot inside the obs-local image
```

## What happens

1. `tools/obs-local.sh` runs the `localhost/obs-local:44` image
   (`tools/obs-local/Containerfile`: fedora-minimal + osc + obs-build +
   podman), privileged, with the repo at `/h` and `~/.config/osc` mounted.
2. `osc build --local-package --alternative-project=home:halcyon041
   Fedora_44 x86_64 anda/<pkg>/<pkg>.spec` — osc uploads the spec to the
   API, the backend computes the buildinfo (buildroot) from the project's
   repo set, and obs-build realizes it locally with the exact package list
   and the project's buildconfig.
3. State (package caches, osc home) persists under `/var/tmp/builds/obs-local/`.

## Isolation model (host safety)

Two modes, neither of which touches the host outside containers and
user-space files:

| mode | where the build runs | root needed |
| --- | --- | --- |
| default (`--vm-type=podman`) | disposable podman container on the host; `--net=none` | no |
| `--container` | chroot inside the privileged `localhost/obs-local:44` image — the same envelope as the repo's anda/mock builds | root inside that container only |

Host-level chroot builds are deliberately unsupported: obs-build's chroot
mode prepares and mounts a buildroot directly on the host, which this repo
never does outside a container. The script also rejects `--vm-type` in
`OBS_LOCAL_EXTRA` so the guarantee can't be bypassed accidentally.

Everything host-native mode writes (all removable):
- `~/.local/lib/build/` + `~/.local/bin/build` — the obs-build engine,
  extracted from the image (inert scripts; `rm -rf` + `osc config general
  build-cmd --delete` reverts).
- `~/.config/osc/oscrc` keys: `build-cmd` (general) and `trusted_prj`
  (apiurl: the project repos whose packages may populate a local buildroot
  — currently `Fedora:44 home:halcyon041 OBS:DefaultKernel`).
- Buildroots and the package cache live under obs-build's own
  `/var/tmp/build-*` directories; osc caches under `~/.cache/obs`.

## Fidelity: podman vs container vs the backend

| mode | isolation | matches backend |
| --- | --- | --- |
| default (podman VM) | `--net=none` container | package set, macros, prjconf AND the network block |
| `--container` (chroot in image) | container + chroot, network open | package set/macros/prjconf; NOT the network block |
| KVM (backend workers) | full VM, no network | what build.opensuse.org actually runs |

OBS build VMs prohibit network access (obs-docu, Security Concepts: "The
VMs prohibit any network access from the running instances"; obs-build's
`--vm-network` flag exists only to turn it ON). Consequences for this repo:

- **Rust source builds** (`cargo_prep_online`/`cargo fetch` in %build),
  **nwg-look** (Go module proxy in %build) and **distroshelf** (meson-cargo
  fetch) **cannot build on OBS as speced** — the default podman VM mode
  reproduces their failure locally (no network), `--container` mode does
  not. They stay on the Actions+Pages/R2
  flow (hybrid policy; vendoring via the obs-service-cargo pattern is the
  eventual OBS-native fix).
- Everything else (the hyprwm stack, binary wrappers, …) builds offline from
  server-fetched sources and works on OBS.
- `anda-srpm-macros` is Terra-only — any rust spec would also fail BR
  resolution on OBS before the network question even arises.
  `cargo-rpm-macros`, `sccache` and `mold` ARE in Fedora 44.

## Limits to keep in mind

- **Known issue (2026-09-25, obs-build 20260901 extracted to ~/.local):**
  the host-native podman-VM run fetched the buildconfig/buildinfo and the
  full package set (507 RPMs, ~292 MB into `/var/tmp/osbuild-packagecache`)
  correctly, then spun at ~100% CPU with zero I/O in obs-build's buildroot
  preparation phase; not debugged further. Server-side expansion — the
  OBS-fidelity part — is proven; for the actual local build, either use
  `--container` (needs an oscrc with a plain user/pass; keyring credentials
  do not cross the container boundary) or simply let build.opensuse.org
  build it (push and watch `osc prjresults`).

- **Buildroot calculation is server-side.** A BuildRequires satisfied only
  by a sibling package that has not been BUILT on OBS yet fails with
  `unresolvable`. Bootstrap order: push the registry first, let OBS build
  roots-up (it schedules by repo availability, like our batches), then
  local-build the leaf packages. `--alternative-project` can point at any
  project whose repo set has the deps.
- **No extra-repo injection in osc build.** Escape hatches:
  `OBS_LOCAL_EXTRA="-x PKG"` (extra packages from the project's repo paths),
  `-p DIR` (prefer local RPMs over downloads), or standalone
  `build --dist <conf> --repo URL …` (a project buildconfig dumps in a
  directly readable format: `osc buildconfig home:halcyon041 Fedora_44`).
- `--offline` reuses the cached buildinfo/buildconfig — handy to iterate on
  a spec without re-asking the server, but it is a cache, not a resolver.
- Keyring-backed osc credentials don't cross the container boundary; the
  oscrc must carry user/password directly.

## Host-native alternative (no container)

Install obs-build on the host (AUR `obs-build` on Arch/CachyOS) and run
`osc build --local-package --alternative-project=home:halcyon041
--vm-type=podman Fedora_44 x86_64 <spec>` directly — podman vm-type needs
no root (obs-build builds a scratch image and bind-mounts the prepared
buildroot). The container route exists so no host packages are required.
