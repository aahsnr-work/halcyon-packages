Name:           zellij
Version:	0.45.1
Release:        1%{?dist}
Summary:        A terminal workspace with batteries included
License:        MIT
URL:            https://github.com/zellij-org/zellij
Source0:        %{url}/releases/download/v%{version}/zellij-x86_64-unknown-linux-musl.tar.gz
BuildArch:      x86_64
BuildRequires:  curl
%description
Terminal workspace with batteries included, built from the upstream release binary.
%prep
%setup -q -c -T -a 0
%define debug_package %{nil}
%install
install -Dm0755 zellij %{buildroot}%{_bindir}/zellij
%files
%{_bindir}/zellij
%changelog
* Sat Sep 19 2026 halcyon-autobuild - 0.45.1-1
- packaged from upstream release binary
