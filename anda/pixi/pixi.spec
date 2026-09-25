# Source build following Terra's pixi.spec: the online cargo prep vendors the
# dependency tree over the network at build time (anda-srpm-macros +
# cargo-rpm-macros, both in Fedora 44, provide the needed macros). The binary
# crate is NOT published to crates.io — the crates.io "pixi" name is an
# unrelated project — so the source is the release tag tarball.
# Was: prebuilt-binary wrapper over the official musl release.
# the vendored crate sources carry Rust inner attributes that the shebang
# mangler misreads, and nothing here is a script to mangle
%undefine __brp_mangle_shebangs
%define debug_package %{nil}
# no debuginfo in the compiled objects either — nothing consumes it and it
# is a large share of compile time on big dependency trees
%define rustflags_debuginfo 0

Name:           pixi
Version:        0.81.0
Release:        1%{?dist}
Summary:        A cross-platform, multi-language package manager and workflow tool
# pixi itself is BSD-3-Clause; the aggregate expression is Terra's for the
# same upstream version — the full per-crate dump ships as LICENSE.dependencies
License:        BSD-3-Clause AND bzip2-1.0.6 AND MPL-2.0 AND Unicode-3.0 AND (Zlib OR Apache-2.0 OR MIT) AND Zlib AND (Unlicense OR MIT) AND (MIT OR Zlib OR Apache-2.0) AND (MIT OR LGPL-3.0-or-later) AND (MIT OR Apache-2.0 OR Zlib) AND (MIT OR Apache-2.0 OR LGPL-2.1-or-later) AND (MIT OR Apache-2.0 OR BSD-1-Clause) AND CDLA-Permissive-2.0 AND (LGPL-3.0-or-later OR MPL-2.0) AND (ISC AND (Apache-2.0 OR ISC) AND OpenSSL) AND (ISC AND (Apache-2.0 OR ISC)) AND ISC AND (CC0-1.0 OR MIT-0 OR Apache-2.0) AND (CC0-1.0 OR MIT-0) AND BSL-1.0 AND (Apache-2.0 OR MIT) AND BSD-2-Clause AND (MIT OR Apache-2.0) AND Unicode-3.0 AND 0BSD AND (0BSD OR MIT OR Apache-2.0) AND Apache-2.0 AND MIT AND (Apache-2.0 OR BSD-2-Clause) AND (Apache-2.0 OR BSL-1.0) AND (Apache-2.0 OR GPL-2.0-only) AND (Apache-2.0 OR ISC OR MIT) AND (Apache-2.0 OR MIT OR Zlib) AND (Apache-2.0 WITH LLVM-exception) AND (Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT) AND (BSD-2-Clause OR Apache-2.0 OR MIT)
URL:            https://pixi.sh
Source0:        https://github.com/prefix-dev/pixi/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  anda-srpm-macros
BuildRequires:  cargo-rpm-macros >= 24
BuildRequires:  mold
# compilation cache server — its cache dir lives on the workspace via the
# mock config's bind mount, shared across all rust source builds
BuildRequires:  sccache

%description
pixi is a cross-platform, multi-language package manager and workflow tool
built on the foundation of the conda ecosystem. It provides developers with an
exceptional experience similar to popular package managers like cargo or npm,
but for any language.

%prep
%autosetup
%cargo_prep_online_sccache

%build
# cache dir on the workspace bind mount (see mock config) — survives across
# builds and is shared by every rust source build
export SCCACHE_DIR=/sccache
%cargo_build
for shell in bash zsh fish; do
    target/rpm/pixi completion --shell $shell > completions.$shell
done

%install
export SCCACHE_DIR=/sccache
install -Dpm755 target/rpm/pixi %{buildroot}%{_bindir}/pixi
install -Dpm644 completions.bash \
    %{buildroot}%{_datadir}/bash-completion/completions/pixi
install -Dpm644 completions.zsh \
    %{buildroot}%{_datadir}/zsh/site-functions/_pixi
install -Dpm644 completions.fish \
    %{buildroot}%{_datadir}/fish/vendor_completions.d/pixi.fish
%{cargo_license_online} > LICENSE.dependencies

%files
%license LICENSE LICENSE.dependencies
%doc README.md CHANGELOG.md
%{_bindir}/pixi
%{_datadir}/bash-completion/completions/pixi
%{_datadir}/zsh/site-functions/_pixi
%{_datadir}/fish/vendor_completions.d/pixi.fish

%changelog
* Thu Sep 24 2026 ahsan <aahsnr041@proton.me> - 0.81.0-1
- source build with the terra cargo macro set, matching Terra's pixi.spec
  (was: prebuilt-binary wrapper over the musl release)
