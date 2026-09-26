# Repackaged from Google's prebuilt tarball on the AUR antigravity-ide
# PKGBUILD pattern (2026-09-26). Proprietary vendor payload, shipped as-is:
#   * /opt/antigravity-ide, launcher script (with per-user flags support)
#     in /usr/bin/antigravity-ide
#   * the AUR's desktop/url-handler/appdata/mime files ride in as local
#     Sources, bash + zsh completions and the pixmaps icon come out of the
#     vendor tree's resources/completions
#   * upstream bundles @parcel/watcher 2.5.1 which triggers a SIGTRAP/
#     coredump on exit — the official prebuilt 2.5.6 node module from npm
#     replaces the faulty binary (parcel-bundler/watcher#216)
#   * license texts copied out of /opt to /usr/share/licenses
# There is no first-party version feed (the download URL embeds a
# non-derivable execution ID); the sweep reads pkgver + the build id off
# the AUR PKGBUILD, whose maintainer tracks upstream.
Name:           antigravity-ide
Version:        2.5.5
Release:        1%{?dist}
Summary:        Agentic development platform from Google
License:        LicenseRef-Google-Antigravity
URL:            https://antigravity.google/
# Google's per-release execution ID in the download URL
%global ide_build 4923483625488384
#!RemoteAsset
Source0:        https://dl.google.com/release2/j0qc3/antigravity/stable/%{version}-%{ide_build}/linux-x64/Antigravity%%20IDE.tar.gz
Source1:        antigravity-ide.sh
Source2:        antigravity-ide.desktop
Source3:        antigravity-ide-url-handler.desktop
Source4:        antigravity-ide.appdata.xml
Source5:        antigravity-ide-workspace.xml
Source6:        https://registry.npmjs.org/@parcel/watcher-linux-x64-glibc/-/watcher-linux-x64-glibc-2.5.6.tgz

ExclusiveArch:  x86_64

# the automatic check stage validates the packaged .desktop files
BuildRequires:  desktop-file-utils

# AUR depends= mapped to Fedora package names
Requires:       alsa-lib
Requires:       at-spi2-core
Requires:       cairo
Requires:       cups-libs
Requires:       curl
Requires:       dbus-libs
Requires:       expat
Requires:       glib2
Requires:       gtk3
Requires:       libsecret
Requires:       libsoup3
Requires:       libX11
Requires:       libxcb
Requires:       libxcomposite
Requires:       libXdamage
Requires:       libxext
Requires:       libxfixes
Requires:       libxkbcommon
Requires:       libxkbfile
Requires:       libxrandr
Requires:       libuuid
Requires:       mesa-libGL
Requires:       nspr
Requires:       nss
Requires:       pango
Requires:       systemd-libs
Requires:       webkit2gtk4.1

%define debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
# the payload must stay byte-identical to the vendor blob
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_mangle_shebangs %{nil}

%description
An agentic development platform from Google, evolving the IDE into the
agent-first era. Repackaged from the official linux-x64 tarball with the
faulty bundled parcel watcher replaced, a system launcher, and the AUR's
desktop integration files.

%prep
%setup -q -c -T
# sources referenced via SOURCE0/SOURCE6 — the vendor tarball keeps its URL
# basename ("Antigravity%%20IDE.tar.gz"), not a spec-derived name
tar -xzf %{SOURCE0}
tar -xzf %{SOURCE6} package/watcher.node

%install
install -dm755 %{buildroot}/opt %{buildroot}%{_bindir} \
    %{buildroot}%{_datadir}/applications %{buildroot}%{_datadir}/metainfo \
    %{buildroot}%{_datadir}/mime/packages \
    %{buildroot}%{_datadir}/bash-completion/completions \
    %{buildroot}%{_datadir}/zsh/site-functions \
    %{buildroot}%{_datadir}/pixmaps %{buildroot}%{_licensedir}/%{name}

cp -a "Antigravity IDE" %{buildroot}/opt/antigravity-ide

# replace the faulty upstream parcel watcher binary
install -Dm755 package/watcher.node \
    %{buildroot}/opt/antigravity-ide/resources/app/node_modules/@parcel/watcher/build/Release/watcher.node

# system launcher with per-user flags support
install -pm755 %{SOURCE1} %{buildroot}%{_bindir}/antigravity-ide

# desktop integration
install -pm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/antigravity-ide.desktop
install -pm644 %{SOURCE3} %{buildroot}%{_datadir}/applications/antigravity-ide-url-handler.desktop
install -pm644 %{SOURCE4} %{buildroot}%{_datadir}/metainfo/antigravity-ide.appdata.xml
install -pm644 %{SOURCE5} %{buildroot}%{_datadir}/mime/packages/antigravity-ide-workspace.xml

# completions + icon out of the vendor tree
install -pm644 "Antigravity IDE/resources/completions/bash/antigravity-ide" \
    %{buildroot}%{_datadir}/bash-completion/completions/antigravity-ide
install -pm644 "Antigravity IDE/resources/completions/zsh/_antigravity-ide" \
    %{buildroot}%{_datadir}/zsh/site-functions/_antigravity-ide
install -pm644 "Antigravity IDE/resources/app/resources/linux/code.png" \
    %{buildroot}%{_datadir}/pixmaps/antigravity-ide.png

# license texts out of /opt
install -pm644 "Antigravity IDE/resources/app/LICENSE.txt" \
    %{buildroot}%{_licensedir}/%{name}/LICENSE.txt
install -pm644 "Antigravity IDE/LICENSES.chromium.html" \
    %{buildroot}%{_licensedir}/%{name}/LICENSES.chromium.html

%files
/opt/antigravity-ide/
%{_bindir}/antigravity-ide
%{_datadir}/applications/antigravity-ide.desktop
%{_datadir}/applications/antigravity-ide-url-handler.desktop
%{_datadir}/metainfo/antigravity-ide.appdata.xml
%{_datadir}/mime/packages/antigravity-ide-workspace.xml
%{_datadir}/bash-completion/completions/antigravity-ide
%{_datadir}/zsh/site-functions/_antigravity-ide
%{_datadir}/pixmaps/antigravity-ide.png
%{_licensedir}/antigravity-ide/

%changelog
* Sat Sep 26 2026 halcyon-autobuild - 2.5.5-1
- initial package: vendor linux-x64 tarball rewrap on the AUR pattern
- parcel watcher 2.5.6 replacement (upstream 2.5.1 SIGTRAP on exit)
- version + build id swept from the AUR PKGBUILD
