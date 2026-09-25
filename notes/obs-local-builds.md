# Local OBS-equivalent builds (tools/obs-local.sh)

Build a halcyon-packages spec locally the way build.opensuse.org would:
same build config, same repo set (Fedora:44 + the project's own packages),
same dependency expansion — via `osc build` + obs-build inside podman.

```bash
tools/obs-local.sh glaze                 # chroot mode (fast, default)
tools/obs-local.sh --faithful glaze      # --vm-type=podman, --net=none
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

## Fidelity: chroot vs podman vs the backend

| mode | isolation | matches backend |
| --- | --- | --- |
| chroot (default) | none — network open | package set, macros, prjconf; NOT the network block |
| `--vm-type=podman` (`--faithful`) | `--net=none` | adds the network block; closest practical local match |
| KVM (backend workers) | full VM, no network | what build.opensuse.org actually runs |

OBS build VMs prohibit network access (obs-docu, Security Concepts: "The
VMs prohibit any network access from the running instances"; obs-build's
`--vm-network` flag exists only to turn it ON). Consequences for this repo:

- **Rust source builds** (`cargo_prep_online`/`cargo fetch` in %build),
  **nwg-look** (Go module proxy in %build) and **distroshelf** (meson-cargo
  fetch) **cannot build on OBS as speced** — `--faithful` reproduces their
  failure locally, chroot mode does not. They stay on the Actions+Pages/R2
  flow (hybrid policy; vendoring via the obs-service-cargo pattern is the
  eventual OBS-native fix).
- Everything else (the hyprwm stack, binary wrappers, …) builds offline from
  server-fetched sources and works on OBS.
- `anda-srpm-macros` is Terra-only — any rust spec would also fail BR
  resolution on OBS before the network question even arises.
  `cargo-rpm-macros`, `sccache` and `mold` ARE in Fedora 44.

## Limits to keep in mind

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
