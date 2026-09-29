# Go source build in this repo's house style (nwg-look pattern: plain go
# build with modules fetched from the Go proxy at build time) instead of
# Terra's go2rpm macro machinery — this repo ships bin-only Go packages.
Name:           asdf
Version:        0.20.2
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        Extendable version manager with support for Ruby, Node.js, Elixir, Erlang & more

License:        MIT
URL:            https://github.com/asdf-vm/asdf
Source0:        %{url}/archive/v%{version}/asdf-%{version}.tar.gz

BuildRequires:  golang

%description
Extendable version manager with support for Ruby, Node.js, Elixir, Erlang
& more. Single static Go binary; plugins provide the actual language
toolchain management.

%prep
%autosetup

%build
# the source carries the release version; pin it to the package version at
# link time anyway
export GOFLAGS="-mod=mod"
go build -o asdf -ldflags "-X main.version=%{version}" ./cmd/asdf

%install
install -m 0755 -vd %{buildroot}%{_bindir}
install -m 0755 asdf %{buildroot}%{_bindir}/asdf

%files
%license LICENSE
%doc README.md
%{_bindir}/asdf

%changelog
* Mon Sep 28 2026 ahsan <aahsnr041@proton.me> - 0.20.2-1
- initial package (Go source build, house nwg-look pattern)
