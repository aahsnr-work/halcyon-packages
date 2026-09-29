# Vendor rewrap of the RPM Proton AG publishes in their official Fedora
# repository (repo.protonvpn.com/fedora-44-stable) — upstream ships the RPM,
# so a rewrap is the sanctioned path, and the payload re-installs verbatim
# (rpm2cpio extract). Versioned by the custom sweep feed: ProtonVPN/proton-vpn-daemon
# tags, HEAD-probing the official repo RPM URL zotero-style so a tag whose
# RPM build has not landed yet never bumps the spec.
%global             pv_fc 44
%global             pv_rel 1
%global             debug_package %{nil}
Name:               proton-vpn-daemon
Version:            0.13.8
Release:            1%{?dist}
Summary:            Proton VPN root daemon (split tunneling D-Bus service)
License:            GPL-3.0-or-later
URL:                https://github.com/ProtonVPN/proton-vpn-daemon
#!RemoteAsset
BuildArch:          noarch
Source0:            https://repo.protonvpn.com/fedora-%{pv_fc}-stable/%{name}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm
BuildRequires:      systemd-rpm-macros
BuildRequires:      python3-devel
Requires:           python3-bcc
Requires:           python3-dbus-fast
Requires:           python3-packaging
Requires:           python3-proton-vpn-api-core >= 5.3.1
Requires:           python3-psutil
Requires:           python3-systemd
Requires:           systemd
Requires:           wireguard-tools
%description
The Proton VPN daemon: split-tunneling D-Bus service consumed by the
GUI app and CLI. Repacked from Proton's official Fedora repository.

%prep
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm | cpio -idm --quiet
test -d usr/lib/python3.14/site-packages/proton/vpn/daemon

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}%{_prefix} %{buildroot}%{_sysconfdir}
cp -a extract/usr/. %{buildroot}%{_prefix}/
cp -a extract/etc/. %{buildroot}%{_sysconfdir}/

%post
%systemd_post me.proton.vpn.split_tunneling.service

%preun
%systemd_preun me.proton.vpn.split_tunneling.service

%postun
%systemd_postun me.proton.vpn.split_tunneling.service

%files
%dir %{_prefix}/lib/python3.14/site-packages/proton
%dir %{_prefix}/lib/python3.14/site-packages/proton/vpn
%{_prefix}/lib/python3.14/site-packages/proton/vpn/daemon/
%{_prefix}/lib/python3.14/site-packages/proton_vpn_daemon-*/
%dir %{_sysconfdir}/dbus-1
%dir %{_sysconfdir}/dbus-1/system.d
%dir %{_sysconfdir}/dbus-1/system-services
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/me.proton.vpn.split_tunneling.conf
%{_sysconfdir}/dbus-1/system-services/me.proton.vpn.split_tunneling.service
%{_unitdir}/me.proton.vpn.split_tunneling.service

%changelog
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 0.13.8-1
- initial package: vendor rewrap of the official repo.protonvpn.com RPM
