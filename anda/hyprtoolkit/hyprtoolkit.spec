# Ported from LionHeartP/hyprlandRPM (the C++ Wayland-native GUI toolkit
# behind hyprland-guiutils, hyprpwcenter and hyprshutdown).
%define debug_package %{nil}

Name:           hyprtoolkit
Version:        0.6.0
Release:        1%{?dist}
Summary:        A modern C++ Wayland-native GUI toolkit

License:        BSD-3-Clause
URL:            https://github.com/hyprwm/hyprtoolkit
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  cmake(hyprwayland-scanner)
BuildRequires:  gcc-c++
BuildRequires:  gtest-devel
BuildRequires:  mesa-libEGL-devel
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(absl_flat_hash_map)
BuildRequires:  pkgconfig(aquamarine)
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(gbm)
BuildRequires:  pkgconfig(hyprgraphics)
BuildRequires:  pkgconfig(hyprlang)
BuildRequires:  pkgconfig(hyprutils)
BuildRequires:  pkgconfig(iniparser)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(pango)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols)
BuildRequires:  pkgconfig(xkbcommon)

%description
%{summary}.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       pkgconfig(aquamarine)
Requires:       pkgconfig(cairo)
Requires:       pkgconfig(hyprgraphics)
%description    devel
Development files for %{name}.

%prep
%autosetup -p1

%build
%cmake -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTING=OFF
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%doc README.md
%{_libdir}/lib%{name}.so.%{version}
%{_libdir}/lib%{name}.so.6

%files devel
%{_includedir}/%{name}/
%{_libdir}/lib%{name}.so
%{_libdir}/pkgconfig/%{name}.pc

%changelog
* Thu Sep 25 2026 halcyon-autobump <aahsnr041@proton.me>
- initial import from LionHeartP/hyprlandRPM (explicit Release + changelog,
  no debug packages) — previously supplied by copr lionheartp/Hyprland
