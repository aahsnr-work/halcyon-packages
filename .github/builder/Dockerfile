FROM registry.fedoraproject.org/fedora-minimal:44

# Build context: the repository root (docker build -f .github/builder/Dockerfile .)
# dnf.conf is crafted in .github/builder/ so the image pulls from Fedora 44 +
# updates, plus the Terra repos that package anda and anda-srpm-macros (they
# are not in Fedora proper). Same shape as terrapkg/builder.
COPY .github/builder/dnf.conf /etc/dnf/dnf.conf

RUN sed -i 's/.fc%{fedora}/.fc44/g' /usr/lib/rpm/macros.d/macros.dist && \
    sed -i '/\[fedora\]\|\[updates\]/a enabled=0' /etc/dnf/dnf.conf && \
    cat /usr/share/dnf5/repos.d/fedora-44.repo >> /etc/dnf/dnf.conf && \
    dnf in -y --nogpgcheck --repo=terra terra-gpg-keys && \
    dnf up -y && \
    dnf swap -y systemd-standalone-sysusers systemd && \
    dnf in -y --nogpgcheck --repo=terra --repo=terra-extras \
        anda anda-srpm-macros \
        mock mock-scm \
        createrepo_c rpm-sign gnupg2 \
        rpmdevtools rpm-build \
        dnf5-plugins git-core jq gh \
        unzip wget less mold sudo @buildsys-build && \
    dnf clean packages dbcache

# The halcyon mock config: /etc/mock/halcyon-f44-x86_64.cfg ships with the
# image, so every build (local and CI) uses the same buildroot.
COPY mock/halcyon-f44-x86_64.cfg /etc/mock/halcyon-f44-x86_64.cfg

CMD ["/bin/bash"]
