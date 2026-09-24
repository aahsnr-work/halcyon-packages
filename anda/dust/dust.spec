Name:           dust
Version:	1.2.6
Release:        1%{?dist}
Summary:        A more intuitive version of du
License:        Apache-2.0
URL:            https://github.com/bootandy/dust
Source0:        %{url}/releases/download/v%{version}/dust-v%{version}-x86_64-unknown-linux-musl.tar.gz
BuildArch:      x86_64
BuildRequires:  curl
%description
du + rust = dust. A more intuitive version of du, built from the upstream
release binary (update automation: update.rhai).
%prep
%setup -q -c -T -a 0
%define debug_package %{nil}
%install
install -Dm0755 dust-v%{version}-x86_64-unknown-linux-musl/dust %{buildroot}%{_bindir}/dust
%files
%{_bindir}/dust
%changelog
* Sat Sep 19 2026 halcyon-autobuild - 1.2.6-1
- packaged from upstream release binary
