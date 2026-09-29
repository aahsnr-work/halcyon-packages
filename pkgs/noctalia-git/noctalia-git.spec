# Noctalia desktop shell (v5, C++/meson — no quickshell runtime). Spec follows
# terrapkg/packages' noctalia-nightly recipe, tracking main branch tip.
%global debug_package   %{nil}
%global commit          3b9a4b3b7c6f23e1875eab19bb3812d509a36901
%global shortcommit     %(c=%{commit}; echo ${c:0:7})
%global upstreamname    noctalia

Name:   	noctalia-git
Version:	5.2.0^4.%{shortcommit}
Release:	1%{?dist}
Summary:	A sleek, customizable desktop shell crafted for Wayland

License:	MIT
URL:		https://github.com/noctalia-dev/%{upstreamname}
Source0:	%{url}/archive/%{commit}/%{upstreamname}-%{commit}.tar.gz

BuildRequires:  meson
BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  git
BuildRequires:  desktop-file-utils
BuildRequires:  pipewire-devel
BuildRequires:  sdbus-cpp-devel
BuildRequires:  tomlplusplus-devel
BuildRequires:  json-devel
BuildRequires:  md4c-devel
BuildRequires:  stb-devel
BuildRequires:  wireplumber-devel
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(freetype2)
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(glesv2)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(jemalloc)
BuildRequires:  pkgconfig(libcurl)
BuildRequires:  pkgconfig(libqalculate)
BuildRequires:  pkgconfig(librsvg-2.0)
BuildRequires:  pkgconfig(libsecret-1)
BuildRequires:  pkgconfig(libsodium)
BuildRequires:  pkgconfig(libwebp)
BuildRequires:  pkgconfig(libxml-2.0)
BuildRequires:  pkgconfig(pam)
BuildRequires:  pkgconfig(pango)
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(libjxl)
BuildRequires:  pkgconfig(libical)
BuildRequires:  pkgconfig(sndfile)

Provides:       desktop-notification-daemon
Provides:       PolicyKit-authentication-agent
Conflicts:      noctalia

Requires:       hicolor-icon-theme
Requires:       dejavu-sans-fonts
Requires:       libwebp

Recommends:     ddcutil
Recommends:     gpu-screen-recorder
Recommends:     power-profiles-daemon

%description
A sleek, customizable desktop shell crafted for Wayland.

%prep
%autosetup -n %{upstreamname}-%{commit}

# report the packaged version instead of meson's 'unknown' fallback
sed -i "s/'unknown'/'v%{version}'/g" meson.build

%conf
%meson

%build
%meson_build

%install
%meson_install
install -d %{buildroot}%{_licensedir}/%{name}/third_party
find third_party -type f \( -name "LICENSE*" -o -name "COPYING*" -o -name "NOTICE*" \) | while read -r file; do
    dest_dir="%{buildroot}%{_licensedir}/%{name}/$(dirname "$file")"
    install -d "$dest_dir"
    install -p -m 0644 "$file" "$dest_dir/"
done

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/dev.noctalia.Noctalia.desktop

%files
%doc README.md
%license LICENSE
%{_licensedir}/%{name}/third_party/
%{_bindir}/noctalia
%{_datadir}/noctalia/
%{_datadir}/applications/dev.noctalia.Noctalia.desktop
%{_datadir}/icons/hicolor/scalable/apps/noctalia.svg

%changelog
* Sun Sep 27 2026 halcyon-autoupdate <aahsnr041@proton.me> - 5.1.0^119.ffbe8d5-1
- switch to noctalia-git snapshot tracking main branch
* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 5.1.0-1
- initial packaging, release-tracked (v5.1.0); recipe from Terra's
  noctalia-nightly (terrapkg/packages)
