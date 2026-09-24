# Wrapper over pixi's official prebuilt musl release binary (single static
# executable). Terra builds pixi from source (%cargo_prep_online), which
# needs network access during the RPM build; here the official binary is
# repackaged instead — same upstream release, seconds instead of ~20 minutes.
# The binary generates its own shell completions at build time.
Name:           pixi
Version:        0.81.0
Release:        1%{?dist}
Summary:        A cross-platform, multi-language package manager and workflow tool
# pixi itself is BSD-3-Clause; the static binary also embeds Rust dependency
# code under its own licenses (see terra's pixi.spec for the full SPDX dump)
License:        BSD-3-Clause
URL:            https://pixi.sh
Source0:        https://github.com/prefix-dev/pixi/releases/download/v%{version}/pixi-x86_64-unknown-linux-musl.tar.gz

ExclusiveArch:  x86_64

%description
pixi is a cross-platform, multi-language package manager and workflow tool
built on the foundation of the conda ecosystem. It provides developers with an
exceptional experience similar to popular package managers like cargo or npm,
but for any language.

%prep
%setup -q -c -T -a 0

%install
install -Dpm755 pixi %{buildroot}%{_bindir}/pixi
./pixi completion --shell bash > pixi.bash
./pixi completion --shell zsh > _pixi
./pixi completion --shell fish > pixi.fish
install -Dpm644 pixi.bash %{buildroot}%{_datadir}/bash-completion/completions/pixi
install -Dpm644 _pixi %{buildroot}%{_datadir}/zsh/site-functions/_pixi
install -Dpm644 pixi.fish %{buildroot}%{_datadir}/fish/vendor_completions.d/pixi.fish

%files
%{_bindir}/pixi
%{_datadir}/bash-completion/completions/pixi
%{_datadir}/zsh/site-functions/_pixi
%{_datadir}/fish/vendor_completions.d/pixi.fish
