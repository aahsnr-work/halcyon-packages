# Ported from github.com/LionHeartP/hyprlandRPM (nwg-look/nwg-look.spec, a
# go2rpm spec carrying a maintainer-generated vendor tarball). This repo
# builds from the Go module proxy at build time instead — mock runs with
# network on, the same pattern as this repo's cargo builds — so the go2rpm
# macro machinery, the vendored dependency tarball and the
# bundle_go_deps_for_rpm.sh step are gone. (Careful with comments: rpm
# expands macros inside them, so never mention go/forge macros textually.)
Name:           nwg-look
Version:        1.1.1
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        GTK3 settings editor adapted to work in the wlroots environment

License:        MIT
URL:            https://github.com/nwg-piotr/nwg-look
Source0:        %{url}/archive/v%{version}/nwg-look-%{version}.tar.gz

BuildRequires:  golang
BuildRequires:  desktop-file-utils
BuildRequires:  pkgconfig(cairo-gobject)
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(gdk-3.0)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gobject-2.0)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(pango)

Requires:       /usr/bin/gsettings
Requires:       xcur2png

%description
GTK3 settings editor adapted to work in the wlroots environment.

prep-stage setup follows

%build
# modules are fetched from the Go proxy during the build (mock runs with
# network on; nothing is vendored or downloaded in %prep)
export GOFLAGS="-mod=mod"
go build -o nwg-look .

%install
install -m 0755 -vd %{buildroot}%{_bindir}
install -m 0755 nwg-look %{buildroot}%{_bindir}/
install -Dpm0644 stuff/main.glade -t %{buildroot}%{_datadir}/nwg-look
install -Dpm0644 langs/* -t %{buildroot}%{_datadir}/nwg-look/langs
install -Dpm0644 stuff/nwg-look.desktop -t %{buildroot}%{_datadir}/applications
install -Dpm0644 stuff/nwg-look.svg -t %{buildroot}%{_datadir}/pixmaps

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license LICENSE
%doc README.md
%{_bindir}/nwg-look
%{_datadir}/%{name}/
%{_datadir}/applications/nwg-look.desktop
%{_datadir}/pixmaps/nwg-look.svg

%changelog
* Thu Sep 24 2026 halcyon-autobump <aahsnr041@proton.me> - 1.1.1-1
- ported from LionHeartP/hyprlandRPM; Go modules fetched at build time
  instead of a vendor tarball
