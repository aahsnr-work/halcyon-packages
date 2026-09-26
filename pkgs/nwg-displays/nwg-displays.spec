# Built from source (pure-Python, setuptools setup.py) following the Arch
# PKGBUILD idioms (2026-09-26): py3_build/py3_install, the repo's desktop
# file and SVG icon, upstream entry points nwg-displays, nwg-displays-apply
# and nwg-displays-toggle-wallpapers.
Name:           nwg-displays
Version:        0.4.4
Release:        1%{?dist}
Summary:        Output configuration utility for Hyprland and Sway
License:        MIT
URL:            https://github.com/nwg-piotr/nwg-displays
#!RemoteAsset
Source0:        https://github.com/nwg-piotr/nwg-displays/archive/refs/tags/v%{version}/nwg-displays-%{version}.tar.gz

BuildArch:      noarch

# the automatic check stage validates the packaged .desktop files
BuildRequires:  desktop-file-utils
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:       python3-gobject
Requires:       python3-i3ipc
Requires:       gtk3
Requires:       gtk-layer-shell
Recommends:     wlr-randr

%define debug_package %{nil}
%global _build_id_links none

%description
nwg-displays is a GTK3 output configuration utility for the Sway and
Hyprland compositors: arrange monitors, set modes, scales and positions,
and apply profiles.

%prep
%autosetup -n nwg-displays-%{version}

%build
%py3_build

%install
%py3_install

install -Dm644 nwg-displays.desktop \
    %{buildroot}%{_datadir}/applications/nwg-displays.desktop
install -Dm644 nwg-displays.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/nwg-displays.svg

%files
%{python3_sitelib}/nwg_displays/
%{python3_sitelib}/nwg_displays-%{version}*.egg-info/
%{_bindir}/nwg-displays
%{_bindir}/nwg-displays-apply
%{_bindir}/nwg-displays-toggle-wallpapers
%{_datadir}/applications/nwg-displays.desktop
%{_datadir}/icons/hicolor/scalable/apps/nwg-displays.svg

%changelog
* Sat Sep 26 2026 halcyon-autobuild - 0.4.3-1
- initial package: pure-Python source build, desktop file + SVG icon from
  the upstream tree
