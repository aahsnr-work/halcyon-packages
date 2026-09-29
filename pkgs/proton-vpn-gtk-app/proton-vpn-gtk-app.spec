# Vendor rewrap of the RPM Proton AG publishes in their official Fedora
# repository (repo.protonvpn.com/fedora-44-stable) — upstream ships the RPM,
# so a rewrap is the sanctioned path, and the payload re-installs verbatim
# (rpm2cpio extract). Versioned by the custom sweep feed: ProtonVPN/proton-vpn-gtk-app
# tags, HEAD-probing the official repo RPM URL zotero-style so a tag whose
# RPM build has not landed yet never bumps the spec.
%global             pv_fc 44
%global             pv_rel 1
%global             debug_package %{nil}
Name:               proton-vpn-gtk-app
Version:            4.18.5
Release:            1%{?dist}
Summary:            Proton VPN GTK4 desktop client
License:            GPL-3.0-or-later
URL:                https://github.com/ProtonVPN/proton-vpn-gtk-app
#!RemoteAsset
BuildArch:          noarch
Source0:            https://repo.protonvpn.com/fedora-%{pv_fc}-stable/%{name}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm
BuildRequires:      python3-devel
Requires:           gtk4
Requires:           libnotify
Requires:           librsvg2
Requires:           python3-dbus
Requires:           python3-gobject
Requires:           python3-packaging
Requires:           python3-proton-vpn-api-core >= 5.8.1
%description
The Proton VPN GTK desktop application (v4 app), talking to the root
daemon over D-Bus. Repacked from Proton's official Fedora repository.

%prep
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm | cpio -idm --quiet
test -d usr/lib/python3.14/site-packages/proton/vpn/app

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}%{_prefix}
cp -a extract/usr/. %{buildroot}%{_prefix}/

%files
%dir %{_prefix}/lib/python3.14/site-packages/proton
%dir %{_prefix}/lib/python3.14/site-packages/proton/vpn
%{_prefix}/lib/python3.14/site-packages/proton/vpn/app/
%{_prefix}/lib/python3.14/site-packages/proton_vpn_gtk_app-*/
%{_bindir}/protonvpn-app
%{_datadir}/applications/proton.vpn.app.gtk.desktop
%{_datadir}/icons/hicolor/scalable/apps/proton-vpn-logo.svg

%changelog
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 4.18.5-1
- initial package: vendor rewrap of the official repo.protonvpn.com RPM
