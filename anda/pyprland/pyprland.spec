# Ported from the AUR PKGBUILD (aur.archlinux.org, h=pyprland) on 2026-09-22
# and adapted to Fedora RPM idioms. Follows the PKGBUILD's build flow:
# python -m build --wheel -> %pyproject_wheel; the compiled C client
# (client/pypr-client) is built with gcc and installed next to the Python
# entry points. Runtime deps mirror the PKGBUILD's depends/optdepends.
# The old halcyon-only systemd user unit was dropped (not in the PKGBUILD).
Name:           pyprland
Version:        3.4.4
Release:        1%{?dist}
Summary:        Hyprland companion daemon and CLI
License:        MIT
URL:            https://github.com/hyprland-community/pyprland
Source0:        %{url}/archive/refs/tags/%{version}/pyprland-%{version}.tar.gz

BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-devel
BuildRequires:  gcc
# PKGBUILD depends= (Arch names -> Fedora)
Requires:       python3-aiofiles
Requires:       python3-aiohttp
Requires:       python3-pillow
# PKGBUILD optdepends=: python-questionary is needed by pypr-quickstart
Recommends:     python3-questionary

%description
Pyprland extends Hyprland with dropped-in Python "plugins": pypr dashboards,
scratchpads, expose, and more.

%prep
%forgeautosetup -p1 -n pyprland-%{version}

%generate_buildrequires
%pyproject_buildrequires

%define debug_package %{nil}
%build
%pyproject_wheel
# PKGBUILD build(): cd client && ${CC:-gcc} -o pypr-client pypr-client.c
gcc -o pypr-client client/pypr-client.c

%install
%pyproject_install
# PKGBUILD package(): install the compiled client and the license
install -Dpm755 pypr-client %{buildroot}%{_bindir}/pypr-client
install -Dpm644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

%files -f %pyproject_files
%license %{_licensedir}/%{name}/LICENSE
%{_bindir}/pypr
%{_bindir}/pypr-gui
%{_bindir}/pypr-quickstart
%{_bindir}/pypr-client
