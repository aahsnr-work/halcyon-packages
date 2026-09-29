# Vendor rewrap of the RPM Proton AG publishes in their official Fedora
# repository (repo.protonvpn.com/fedora-44-stable) — upstream ships the RPM,
# so a rewrap is the sanctioned path, and the payload re-installs verbatim
# (rpm2cpio extract). Versioned by the custom sweep feed: ProtonVPN/python-proton-vpn-api-core
# tags, HEAD-probing the official repo RPM URL zotero-style so a tag whose
# RPM build has not landed yet never bumps the spec.
%global             pv_fc 44
%global             pv_rel 1
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

Name:               python3-proton-vpn-api-core
Version:            5.8.3
Release:            1%{?dist}
Summary:            Proton VPN API facade with the integrated NetworkManager backend and Rust services
License:            GPL-3.0-or-later
URL:                https://github.com/ProtonVPN/python-proton-vpn-api-core
#!RemoteAsset
Source0:            https://repo.protonvpn.com/fedora-%{pv_fc}-stable/%{name}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.x86_64.rpm
ExclusiveArch:      x86_64

BuildRequires:      systemd-rpm-macros
Requires:           NetworkManager
Requires:           NetworkManager-openvpn
Requires:           NetworkManager-openvpn-gnome
Requires:           gobject-introspection
Requires:           python3-dbus-fast
Requires:           python3-distro
Requires:           python3-fido2
Requires:           python3-gobject
Requires:           python3-jinja2
Requires:           python3-packaging
Requires:           python3-proton-core >= 0.5.0
Requires:           python3-pynacl
Requires:           python3-sentry-sdk
Requires:           systemd
%description
The proton-vpn-api-core facade over the Proton VPN services, with the
integrated NetworkManager backend and the Rust nm-protun / kill-switch
helper services. Repacked from Proton's official Fedora repository.

%prep
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.x86_64.rpm | cpio -idm --quiet
test -d usr/lib64/python3.14/site-packages/proton/vpn

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}%{_prefix}
cp -a extract/usr/. %{buildroot}%{_prefix}/

%post
%systemd_post proton-vpn-kill-switch-boot.service

%preun
%systemd_preun proton-vpn-kill-switch-boot.service

%postun
%systemd_postun proton-vpn-kill-switch-boot.service

%files
%%{_prefix}/lib64/python3.14/site-packages/proton/
%%{_prefix}/lib64/python3.14/site-packages/proton_vpn_api_core-*/
%{_libexecdir}/nm-protun-service
%{_libexecdir}/proton-vpn-kill-switch-service
%{_prefix}/lib/NetworkManager/VPN/nm-protun.name
%{_unitdir}/proton-vpn-kill-switch-boot.service
%{_datadir}/dbus-1/system-services/me.proton.vpn.kill_switch.service
%{_datadir}/dbus-1/system.d/me.proton.vpn.kill_switch.conf
%{_datadir}/dbus-1/system.d/nm-protun-service.conf

%changelog
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 5.8.3-1
- initial package: vendor rewrap of the official repo.protonvpn.com RPM
