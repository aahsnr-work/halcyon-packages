# Vendor install of the prebuilt adw-gtk3 theme bundle from the upstream
# release asset (the file upstream documents as "extract into /usr/share/
# themes"): adw-gtk3/ and adw-gtk3-dark/ sit at the tarball's top level.
# v6.x builds from source via meson with the sass binary — dart-sass, which
# Fedora 44 does not package (only sassc) — so the release bundle is the
# only viable source here, and it is the upstream distribution artifact.
# The bundle carries no license file; LICENSE ships as Source1 from the tag
# (LGPL-2.1, "or any later version" wording).
Name:           adw-gtk3
Version:        6.5
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        GTK3 theme styled after Libadwaita
BuildArch:      noarch
License:        LGPL-2.1-or-later
URL:            https://github.com/lassekongo83/adw-gtk3
Source0:        %{url}/releases/download/v%{version}/adw-gtk3v%{version}.tar.xz
Source1:        %{url}/raw/v%{version}/LICENSE

%description
adw-gtk3 is a GTK3 theme that makes GTK3 applications look like Libadwaita
applications. This package installs the light (adw-gtk3) and dark
(adw-gtk3-dark) variants system-wide; select them with a theme switcher
(e.g. nwg-look) or gsettings gtk-theme.

%prep
%setup -q -c
cp %{SOURCE1} LICENSE

%install
mkdir -p %{buildroot}%{_datadir}/themes
cp -a adw-gtk3 adw-gtk3-dark %{buildroot}%{_datadir}/themes/

%files
%{_datadir}/themes/adw-gtk3/
%{_datadir}/themes/adw-gtk3-dark/
%license LICENSE

%changelog
* Mon Sep 28 2026 halcyon-autoupdate <aahsnr041@proton.me> - 6.5-1
- initial packaging from the prebuilt release bundle
