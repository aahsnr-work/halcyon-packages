Name:           yazi
Version:        26.9.1
Release:        1%{?dist}
Summary:        Blazing fast terminal file manager
License:        MIT
URL:            https://github.com/sxyazi/yazi
Source0:        %{url}/releases/download/v%{version}/yazi-x86_64-unknown-linux-gnu.zip
BuildArch:      x86_64
BuildRequires:  curl
BuildRequires:  unzip
%description
Blazing fast terminal file manager, built from the upstream release binary.
%prep
%setup -q -c -T -a 0
%define debug_package %{nil}
%install
install -Dm0755 yazi-x86_64-unknown-linux-gnu/yazi %{buildroot}%{_bindir}/yazi
install -Dm0755 yazi-x86_64-unknown-linux-gnu/ya %{buildroot}%{_bindir}/ya
%files
%{_bindir}/yazi
%{_bindir}/ya
%changelog
* Sat Sep 19 2026 halcyon-autobuild - 26.9.1-1
- packaged from upstream release binary
