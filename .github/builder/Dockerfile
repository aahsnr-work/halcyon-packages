FROM registry.fedoraproject.org/fedora-minimal:44

# Build context: the repository root (docker build -f .github/builder/Dockerfile .)
# dnf.conf adds the Terra repos that package anda (they are not in Fedora
# proper) but leaves them disabled — the --repo= flags below use them per
# transaction, exactly like terrapkg/builder. The stock
# /etc/yum.repos.d/fedora*.repo keep providing Fedora 44 + updates.
COPY .github/builder/dnf.conf /etc/dnf/dnf.conf

RUN dnf in -y --nogpgcheck --repo=terra terra-gpg-keys && \
    dnf up -y && \
    dnf swap -y systemd-standalone-sysusers systemd && \
    dnf in -y \
        anda anda-srpm-macros \
        mock mock-scm \
        createrepo_c rpm-sign gnupg2 \
        rpmdevtools rpm-build \
        dnf5-plugins git-core jq gh rclone \
        unzip wget less mold sudo @buildsys-build && \
    dnf clean packages dbcache && \
    # mock unmounts chroot mounts by calling /usr/bin/umount, which Fedora
    # ships setuid-root; on some host kernels (e.g. CachyOS 7.x) the setuid
    # loader fails with "cannot apply additional memory protection" — and
    # mock always runs as root here, so the bit is pointless anyway
    chmod u-s /usr/bin/umount

# The halcyon mock config: /etc/mock/halcyon-f44-x86_64.cfg ships with the
# image, so every build (local and CI) uses the same buildroot.
COPY mock/halcyon-f44-x86_64.cfg /etc/mock/halcyon-f44-x86_64.cfg

CMD ["/bin/bash"]
