# Ported from LionHeartP/hyprlandRPM. Pinned to the version the dependents
# (hyprland, hyprshutdown) are validated against; upstream is already on the
# 9.x series — the daily sweep proposes the bump and CI validates it against
# the dependents in one run.
%define debug_package %{nil}

Name:           glaze
Version:        9.0.0
Release:        1%{?dist}
Summary:        Extremely fast, in memory, JSON and interface library

License:        MIT
URL:            https://github.com/stephenberry/glaze
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++

%description
%{summary}.

%package        devel
Summary:        Development files for %{name}
BuildArch:      noarch
Provides:       %{name}-static = %{version}-%{release}
%description    devel
Development files for %{name}.

%prep
%autosetup -p1

%build
%cmake \
    -Dglaze_INSTALL_CMAKEDIR=%{_datadir}/cmake/%{name} \
    -Dglaze_DISABLE_SIMD_WHEN_SUPPORTED:BOOL=ON \
    -Dglaze_DEVELOPER_MODE:BOOL=OFF \
    -Dglaze_ENABLE_FUZZING:BOOL=OFF
%cmake_build

%install
%cmake_install

%files
%license LICENSE

%files devel
%doc README.md
%{_datadir}/cmake/%{name}/
%{_includedir}/%{name}/

%changelog
* Fri Sep 25 2026 halcyon-autobump <aahsnr041@proton.me>
- initial import from LionHeartP/hyprlandRPM (explicit Release + changelog,
  no debug packages) — previously supplied by copr lionheartp/Hyprland
