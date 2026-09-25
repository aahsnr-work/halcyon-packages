Name:           hyprland-protocols
Version:	0.7.1
Release:        1%{?dist}
Summary:        Wayland protocol extensions for Hyprland
BuildArch:      noarch

License:        BSD-3-Clause
URL:            https://github.com/hyprwm/hyprland-protocols
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake

%description
%{summary}.

%package        devel
Summary:        Wayland protocol extensions for Hyprland

%description    devel
%{summary}.


%prep
%autosetup -p1


%build
# upstream switched from meson to cmake at v0.7.1 (the tarball carries
# CMakeLists.txt; it installs the protocol XMLs and the pkg-config file)
%cmake
%cmake_build


%install
%cmake_install


%files devel
%license LICENSE
%doc README.md
%{_datadir}/pkgconfig/%{name}.pc
%{_datadir}/%{name}/


%changelog
* Wed Sep 23 2026 halcyon-autobump <aahsnr041@proton.me>
- converted to an explicit Release and changelog for the anda build
