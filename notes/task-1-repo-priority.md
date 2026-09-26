# Task 1 — this Copr repo gets the highest install priority

Requirement: packages built here must never resolve from Fedora, Terra or
another Copr on consumer machines; the hyprwm stack in particular (everything
`hypr*` plus glaze/hyprwire/hyprtoolkit) installs from this repo.

## What was done

`repo/halcyon.repo` — a checked-in dnf drop-in for consumers:

- baseurl `https://download.copr.fedorainfracloud.org/results/aahsnr-work/halcyon/fedora-$releasever-$basearch/`
- Copr's project GPG key (`pubkey.gpg`), gpgcheck on
- **`priority=1`** — dnf prefers the lowest priority number (Fedora/Terra run
  at the default 99), so every package we build shadows same-named packages
  from anywhere else.

Why a checked-in file instead of `dnf copr enable`: the copr plugin does not
set a priority, and "must not install from Fedora/Terra" is exactly what a
priority encodes. Consumers either install the drop-in directly or run
`dnf copr enable aahsnr-work/halcyon fedora-44` and merge the `priority=1`
line into the generated file.

## Build-time side

Inside the Copr buildroot the project's own repo already outranks the chroot's
external repos (lionheartp bootstrap, Terra), so wave N+1 builds against wave
N's output — no change needed there.

## Verified

- Fedora 44 conflict set confirmed: `hyprlang 0.6.4`, `hyprutils 0.7.1`,
  `zoxide 0.9.8`, `fd-find 10.4.2`, `cliphist 0.7.0` — all older than (or
  equal to, cliphist) our builds, and all lose to `priority=1`.
- chafa's note ("Fedora carries an older chafa") applies repo-wide now.
