# Source build of cava (karlstav/cava) from the upstream release tarball —
# releases ship no rpm (the old one is gone upstream). autotools build with
# the pre-generated configure included in the tarball; all optional audio
# backends that Fedora provides are enabled via their BuildRequires.
Name:           cava
Version:        1.0.0
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        Console-based audio visualizer for ALSA, PipeWire and PulseAudio
License:        MIT
URL:            https://github.com/karlstav/cava
Source0:        %{url}/releases/download/%{version}/cava-%{version}.tar.gz

ExclusiveArch:  x86_64

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  alsa-lib-devel
BuildRequires:  fftw-devel
BuildRequires:  pipewire-devel
BuildRequires:  pulseaudio-libs-devel
BuildRequires:  jack-audio-connection-kit-devel
BuildRequires:  iniparser-devel

%description
CAVA (Cross-platform Audio Visualizer) renders bar-spectrum audio
visualizations in the terminal, reading ALSA, PipeWire, PulseAudio or JACK
output directly.

%prep
%autosetup -p1

%build
%configure
%make_build

%install
%make_install

%files
%license LICENSE
%doc README.md
# cava 1.0.0's tarball ships no changelog/man page; make install puts the
# console font into /usr/share/consolefonts (cava_font__DATA)
%{_bindir}/cava
%{_datadir}/consolefonts/cava.psf

%changelog
* Fri Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 1.0.0-1
- changelog retro-added (the spec predates the written-changelog rule)
