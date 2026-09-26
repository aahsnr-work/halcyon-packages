# Task 8 — is dnf.conf in .github/builder still needed?

**No — already deleted** during the 2026-09-25 audit, before this TODO file
existed. Its only purpose was enabling the Terra repos inside the builder
image to install `anda` and `anda-srpm-macros`; the image no longer installs
anda (and the Copr buildroot gets Terra from the chroot repo list). The
Dockerfile no longer COPYs it, so the file was dead. Nothing references it.
