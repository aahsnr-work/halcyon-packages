# Ported from terrapkg/packages frawhide (anda/apps/zotero) on 2026-09-22 and
# adapted to this repo's Copr custom-source pipeline. Deviations from upstream:
#   * Source0 is the OFFICIAL prebuilt Zotero tarball instead of building from
#     the git tag: upstream's %prep (%git_clone + npm install) and %build
#     (npm run clean-build) fetch transient CI artifacts from
#     zotero-download.s3.amazonaws.com/ci/... which are gone (403) for the
#     current tags — the npm build cannot complete reliably for anyone, let
#     alone unattended. The official tarball is the output of the same
#     dir_build and carries zotero.desktop + the icons, so every %install and
#     %files line below is upstream's, just pointing at the unpacked tarball.
#   * terra-appstream-helper / %terra_appstream / %desktop_file_install are
#     Terra-build-env macros — replaced with the plain Fedora equivalents
#     (marked inline). %_hicolordir / %_appsdir are defined below so the
#     upstream %install and %files lines stay untouched.
#   * %doc README.md / CONTRIBUTING.md and %license COPYING dropped: the
#     official tarball ships neither.
%global debug_package %{nil}
%global appid org.zotero.Zotero
%global bundledir %{_libdir}/zotero
%global _hicolordir %{_datadir}/icons/hicolor
%global _appsdir %{_datadir}/applications

Name:           zotero
Version:        10.0.3
Release:        2%{?dist}
Summary:        Collect, organize, cite, and share your research sources
URL:            https://www.zotero.org/
License:        AGPL-3.0-or-later
ExclusiveArch:  x86_64

Source0:        https://download.zotero.org/client/release/%{version}/Zotero-%{version}_linux-x86_64.tar.xz
Source1:        %{appid}.metainfo.xml

BuildRequires:  desktop-file-utils
BuildRequires:  appstream

Requires:       gtk3
Requires:       hicolor-icon-theme
Requires:       xdg-utils

Packager:       Cypress Reed <cypress@fyralabs.com>

%description
Zotero is a free, easy-to-use tool to help you collect, organize, cite, and
share research sources.

%prep
%setup -q -c -T -a 0

%install
install -dm755 %{buildroot}%{bundledir}
# upstream: cp -a app/staging/Zotero_linux-*/* %{buildroot}%{bundledir}/
cp -a Zotero_linux-x86_64/* %{buildroot}%{bundledir}/

install -dm755 %{buildroot}%{_bindir}
ln -sr %{buildroot}%{bundledir}/zotero %{buildroot}%{_bindir}/zotero

# upstream: %desktop_file_install -k Exec,Icon -v zotero,zotero -u %U
install -Dpm644 %{buildroot}%{bundledir}/zotero.desktop \
    %{buildroot}%{_appsdir}/zotero.desktop
rm %{buildroot}%{bundledir}/zotero.desktop

for size in 32 64 128; do
    install -Dpm644 %{buildroot}%{bundledir}/icons/icon${size}.png \
        %{buildroot}%{_hicolordir}/${size}x${size}/apps/zotero.png
done

# upstream: %terra_appstream -o %{SOURCE1}
install -Dpm644 %{SOURCE1} %{buildroot}%{_metainfodir}/%{appid}.metainfo.xml

%check
# upstream: %desktop_file_validate -f %{buildroot}%{_appsdir}/zotero.desktop
desktop-file-validate %{buildroot}%{_appsdir}/zotero.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/%{appid}.metainfo.xml

%files
%{_bindir}/zotero
%{bundledir}/
%{_appsdir}/zotero.desktop
%{_hicolordir}/32x32/apps/zotero.png
%{_hicolordir}/64x64/apps/zotero.png
%{_hicolordir}/128x128/apps/zotero.png
%{_metainfodir}/%{appid}.metainfo.xml

%changelog
* Thu Sep 17 2026 Cypress Reed <cypress@fyralabs.com>
- initial commit
