# Ported from github.com/LionHeartP/hyprlandRPM (qt6ct/qt6ct.spec): same
# patch, dependencies and file lists. The forgemeta machinery is inlined
# (Source0 = the GitLab archive of the pinned commit) and the spec carries an
# explicit Release + changelog instead of rpmautospec.
%global commit 00823e41aa60e8fe266d5aee328e82ad1ad94348

Name:    qt6ct
Version: 0.11
Release: 15%{?dist}
Summary: Qt6 - Configuration Tool

License: BSD-2-Clause
URL:     https://www.opencode.net/trialuser/qt6ct

Source0: %{url}/-/archive/%{commit}/qt6ct-%{commit}.tar.gz
Patch0:  qt6ct-shenanigans.patch

BuildRequires: cmake
BuildRequires: gcc-c++
BuildRequires: qt6-rpm-macros >= %{version}
BuildRequires: qt6-qtbase-devel
BuildRequires: qt6-qtbase-private-devel
BuildRequires: qt6-qtdeclarative-devel
BuildRequires: qt6-linguist
BuildRequires: kf6-kiconthemes-devel
BuildRequires: kf6-kconfig-devel
BuildRequires: cmake(KF6ColorScheme)
BuildRequires: desktop-file-utils

Requires:       kf6-qqc2-desktop-style%{?_isa}
Requires:       qt6-qtsvg%{?_isa}

Obsoletes:      %{name}-kde < 0.10-3
Provides:       %{name}-kde = %{version}-%{release}
Provides:       %{name}-kde%{?_isa} = %{version}-%{release}

%description
This program allows users to configure Qt6 settings (theme, font, icons, etc.)
under DE/WM without Qt integration.

%prep
%autosetup -n qt6ct-%{commit} -p1

%build
%cmake
%cmake_build

%install
%cmake_install

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%doc AUTHORS README.md ChangeLog
%license COPYING
%{_bindir}/%{name}
%{_qt6_plugindir}/platformthemes/libqt6ct.so
%{_qt6_plugindir}/styles/libqt6ct-style.so
%{_datadir}/applications/%{name}.desktop
%dir %{_datadir}/%{name}/
%dir %{_datadir}/%{name}/colors/
%{_datadir}/%{name}/colors/*.conf
%dir %{_datadir}/%{name}/qss/
%{_datadir}/%{name}/qss/*.qss
%{_libdir}/libqt6ct-common.so
%{_libdir}/libqt6ct-common.so.%{version}*

%changelog
* Thu Sep 24 2026 halcyon-autobump <aahsnr041@proton.me> - 0.11-15
- ported from LionHeartP/hyprlandRPM (their -b15 base release)
