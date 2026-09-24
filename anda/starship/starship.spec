Name:           starship
Version:	1.26.0
Release:        1%{?dist}
Summary:        The minimal, blazing-fast, infinitely customizable prompt
License:        ISC
URL:            https://github.com/starship/starship
Source0:        %{url}/releases/download/v%{version}/starship-x86_64-unknown-linux-musl.tar.gz
BuildArch:      x86_64
BuildRequires:  curl
%description
Cross-shell prompt, built from the upstream release binary.
%prep
%setup -q -c -T -a 0
%define debug_package %{nil}
%install
install -Dm0755 starship %{buildroot}%{_bindir}/starship
%files
%{_bindir}/starship
%changelog
* Sat Sep 19 2026 halcyon-autobuild - 1.26.0-1
- packaged from upstream release binary
