Name:           pandoc
Version:	3.11
Release:        1%{?dist}
Summary:        Universal markup converter (upstream release binary)
License:        GPL-2.0-or-later
URL:            https://github.com/jgm/pandoc
Source0:        %{url}/releases/download/%{version}/pandoc-%{version}-linux-amd64.tar.gz
#!RemoteAsset
Source1:        %{url}/raw/%{version}/COPYING.md
ExclusiveArch: x86_64
BuildRequires:  curl
%description
Pandoc converts between markup formats, from the upstream release binary —
packaged because Fedora's pandoc is not continuously updated.
%prep
%setup -q -c -T -a 0
%define debug_package %{nil}
%global _build_id_links none
%install
# vendor tarballs ship no license text; the repo LICENSE rides along
install -Dpm0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/COPYING.md
install -Dm0755 pandoc-%{version}/bin/pandoc %{buildroot}%{_bindir}/pandoc
%files
%license COPYING.md
%{_bindir}/pandoc
%changelog
* Sat Sep 19 2026 halcyon-autobuild - 3.11-1
- packaged from upstream release binary
