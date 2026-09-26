# Built from source following the Arch PKGBUILD (2026-09-26), minus the
# system-electron surgery: Fedora has no electron43 package, so the build
# uses the BUNDLED Electron — electron's own dist is fetched by its
# install.js into node_modules (dependency postinstall scripts are blocked
# by pnpm >= 10, so it is fetched explicitly during the build) and
# electron-builder packs dist/linux-unpacked with it. The packed tree
# lands in /usr/lib/podman-desktop with a /usr/bin wrapper; desktop file,
# appdata and icons come from the source tree.
Name:           podman-desktop
Version:        1.29.3
Release:        1%{?dist}
Summary:        Manage Podman and other container engines from a single UI and tray
License:        Apache-2.0
URL:            https://podman-desktop.io
#!RemoteAsset
Source0:        https://github.com/podman-desktop/podman-desktop/archive/refs/tags/v%{version}/podman-desktop-%{version}.tar.gz

ExclusiveArch:  x86_64

# the automatic check stage validates the packaged .desktop files
BuildRequires:  desktop-file-utils

BuildRequires:  nodejs
BuildRequires:  npm
BuildRequires:  jq
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  python3-setuptools
BuildRequires:  vips-devel
BuildRequires:  lcms2-devel
BuildRequires:  openjpeg-devel

# bundled electron runtime
Requires:       gtk3
Requires:       nss
Requires:       at-spi2-core
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libnotify
Requires:       xdg-utils
Requires:       libsecret
Requires:       podman

%define debug_package %{nil}
%global _build_id_links none

%description
Podman Desktop is an open source graphical tool for developing on
containers and Kubernetes: manage Podman, Docker, Kind and other
container engines from a single UI and tray. Built from source with the
upstream-bundled Electron runtime.

%prep
%autosetup -n podman-desktop-%{version}

%build
# pnpm >= 10 blocks dependency build scripts unless the package.json
# whitelists them (upstream pins none); install with scripts skipped and
# fetch the bundled Electron dist explicitly afterwards
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
npm install -g pnpm@11.15.1

export ELECTRON_SKIP_BINARY_DOWNLOAD=1
pnpm install --no-frozen-lockfile
(cd node_modules/electron && node install.js)

node_modules/.bin/cross-env MODE=production pnpm run build
node_modules/.bin/electron-builder build --linux --x64 --dir \
    --config .electron-builder.config.cjs

%install
install -dm755 %{buildroot}%{_libdir}/%{name} %{buildroot}%{_bindir} \
    %{buildroot}%{_datadir}/applications %{buildroot}%{_datadir}/metainfo \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps \
    %{buildroot}%{_datadir}/icons/hicolor/1024x1024/apps
cp -a dist/linux-unpacked/. %{buildroot}%{_libdir}/%{name}/

# system launcher
cat > %{buildroot}%{_bindir}/podman-desktop <<'EOF'
#!/bin/sh
exec /usr/lib/podman-desktop/podman-desktop "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/podman-desktop

# desktop file: point the upstream flatpak Exec at the system launcher
sed -e 's|^Exec=.*|Exec=/usr/bin/podman-desktop %U|' -e '/^X-Flatpak=/d' \
    .flatpak.desktop > %{buildroot}%{_datadir}/applications/io.podman_desktop.PodmanDesktop.desktop
install -pm644 .flatpak-appdata.xml \
    %{buildroot}%{_datadir}/metainfo/io.podman_desktop.PodmanDesktop.metainfo.xml
install -pm644 buildResources/icon.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/io.podman_desktop.PodmanDesktop.svg
install -pm644 buildResources/icon-512x512.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/io.podman_desktop.PodmanDesktop.png
install -pm644 buildResources/icon.png \
    %{buildroot}%{_datadir}/icons/hicolor/1024x1024/apps/io.podman_desktop.PodmanDesktop.png

%files
%{_libdir}/podman-desktop/
%{_bindir}/podman-desktop
%{_datadir}/applications/io.podman_desktop.PodmanDesktop.desktop
%{_datadir}/metainfo/io.podman_desktop.PodmanDesktop.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/io.podman_desktop.PodmanDesktop.svg
%{_datadir}/icons/hicolor/512x512/apps/io.podman_desktop.PodmanDesktop.png
%{_datadir}/icons/hicolor/1024x1024/apps/io.podman_desktop.PodmanDesktop.png

%changelog
* Sat Sep 26 2026 halcyon-autobuild - 1.29.3-1
- initial package: source build with bundled Electron 43.2.0
- pnpm 11 via npm, electron dist fetched by install.js (pnpm build-script
  gate), electron-builder --dir packing
