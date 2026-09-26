# Upstream is Go (go.senan.xyz/cliphist), not Rust — the first draft here
# wrongly assumed a cargo build because crates.io 404s. Modeled on
# LionHeartP/hyprlandRPM's go2rpm spec, adapted the nwg-look way: no go2rpm
# macro machinery and no maintainer-generated vendor tarball — the modules
# are fetched from the Go proxy during the build stage (mock runs with network on;
# nothing is vendored or downloaded in prep). The version string is
# embedded by upstream via go:embed version.txt, so no ldflags are needed.
%define debug_package %{nil}

Name:           cliphist
Version:        0.7.0
Release:        1%{?dist}
Summary:        Wayland clipboard manager with support for multimedia

License:        GPL-3.0-only
URL:            https://github.com/sentriz/cliphist
Source0:        %{url}/archive/refs/tags/v%{version}/cliphist-%{version}.tar.gz

BuildRequires:  golang

Requires:       wl-clipboard
Requires:       xdg-utils

%description
Wayland clipboard manager with support for multimedia.

%prep
%autosetup -p1

%build
export GOFLAGS="-mod=mod"
go build -o cliphist .

%install
install -Dpm0755 cliphist %{buildroot}%{_bindir}/cliphist

%files
%license LICENSE
%doc CHANGELOG.md readme.md
%{_bindir}/cliphist

%changelog
* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 0.7.0-1
- initial packaging (Go source build from the release tag tarball; first
  draft wrongly assumed a cargo build)
