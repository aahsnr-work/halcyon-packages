# Vendor rewrap of the RPM Proton AG publishes in their official Fedora
# repository (repo.protonvpn.com/fedora-44-stable) — upstream ships the RPM,
# so a rewrap is the sanctioned path, and the payload re-installs verbatim
# (rpm2cpio extract). Versioned by the custom sweep feed: ProtonVPN/python-proton-keyring-linux
# tags, HEAD-probing the official repo RPM URL zotero-style so a tag whose
# RPM build has not landed yet never bumps the spec.
%global             pv_fc 44
%global             pv_rel 1
%global             debug_package %{nil}
Name:               python3-proton-keyring-linux
Version:            0.2.3
Release:            1%{?dist}
Summary:            Proton keyring component for Linux desktops
License:            GPL-3.0-or-later
URL:                https://github.com/ProtonVPN/python-proton-keyring-linux
#!RemoteAsset
BuildArch:          noarch
Source0:            https://repo.protonvpn.com/fedora-%{pv_fc}-stable/%{name}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm
BuildRequires:      python3-devel
Requires:           gnome-keyring
Requires:           python3-keyring
Requires:           python3-proton-core
Requires:           python3-secretstorage
%description
The proton-keyring-linux component: credential storage through the
desktop keyring (libsecret / secret service). Repacked from Proton's
official Fedora repository.

%prep
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm | cpio -idm --quiet
test -d usr/lib/python3.14/site-packages/proton/keyring_linux

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}%{_prefix}
cp -a extract/usr/. %{buildroot}%{_prefix}/

%files
%dir %{_prefix}/lib/python3.14/site-packages/proton
%{_prefix}/lib/python3.14/site-packages/proton/keyring_linux/
%{_prefix}/lib/python3.14/site-packages/proton_keyring_linux-*/

%changelog
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 0.2.3-1
- initial package: vendor rewrap of the official repo.protonvpn.com RPM
