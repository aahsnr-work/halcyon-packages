# Vendor rewrap of the RPM Proton AG publishes in their official Fedora
# repository (repo.protonvpn.com/fedora-44-stable) — upstream ships the RPM,
# so a rewrap is the sanctioned path, and the payload re-installs verbatim
# (rpm2cpio extract). Versioned by the custom sweep feed: ProtonVPN/python-proton-core
# tags, HEAD-probing the official repo RPM URL zotero-style so a tag whose
# RPM build has not landed yet never bumps the spec.
%global             pv_fc 44
%global             pv_rel 1
%global             debug_package %{nil}
Name:               python3-proton-core
Version:            0.7.4
Release:            1%{?dist}
Summary:            Core logic shared by every Proton component (sessions, SSO, transports)
License:            GPL-3.0-or-later
URL:                https://github.com/ProtonVPN/python-proton-core
#!RemoteAsset
BuildArch:          noarch
Source0:            https://repo.protonvpn.com/fedora-%{pv_fc}-stable/%{name}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm
BuildRequires:      python3-devel
Requires:           python3-aiohttp
Requires:           python3-bcrypt
Requires:           python3-gnupg
Requires:           python3-importlib-metadata
Requires:           python3-pyOpenSSL
Requires:           python3-requests
%description
The proton-core component: session handling, SSO authentication and
transport logic used by the other Proton python components. Repacked from
Proton's official Fedora repository.

%prep
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm | cpio -idm --quiet
test -d usr/lib/python3.14/site-packages/proton

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}%{_prefix}
cp -a extract/usr/. %{buildroot}%{_prefix}/

%files
%dir %{_prefix}/lib/python3.14/site-packages/proton
%{_prefix}/lib/python3.14/site-packages/proton/keyring/
%{_prefix}/lib/python3.14/site-packages/proton/loader/
%{_prefix}/lib/python3.14/site-packages/proton/session/
%{_prefix}/lib/python3.14/site-packages/proton/sso/
%{_prefix}/lib/python3.14/site-packages/proton/utils/
%{_prefix}/lib/python3.14/site-packages/proton/views/
%{_prefix}/lib/python3.14/site-packages/proton_core-*/

%changelog
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 0.7.4-1
- initial package: vendor rewrap of the official repo.protonvpn.com RPM
