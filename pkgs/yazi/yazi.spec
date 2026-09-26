# Source build following Terra's yazi.spec: the yazi workspace is not
# published to crates.io as an installable crate, so the source is the release
# tag tarball and the dependency tree is vendored over the network at build
# time (cargo-rpm-macros, in Fedora 44). The vergen
# build script needs a git sha injected — GitHub tag tarballs carry no .git.
# Was: prebuilt-binary wrapper over the official gnu release zip.
%undefine __brp_mangle_shebangs
%define debug_package %{nil}
# no debuginfo in the compiled objects either — nothing consumes it and it
# is a large share of compile time on big dependency trees
%define rustflags_debuginfo 0

Name:           yazi
Version:        26.9.1
Release:        1%{?dist}
Summary:        Blazing fast terminal file manager
# aggregate expression is Terra's for the same upstream version (unbalanced
# paren in their expression fixed) — the per-crate dump ships as
# LICENSE.dependencies
License:        MIT AND (MIT OR Apache-2.0) AND NCSA AND Unicode-3.0 AND (0BSD OR MIT OR Apache-2.0) AND Apache-2.0 AND ISC AND (Apache-2.0 OR BSL-1.0) AND (Apache-2.0 OR MIT) AND (Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT) AND BSD-2-Clause AND BSD-3-Clause AND (BSD-2-Clause OR Apache-2.0 OR MIT) AND (BSD-3-Clause OR Apache-2.0) AND BSL-1.0 AND CC0-1.0 AND (CC0-1.0 OR Apache-2.0) AND ISC AND (MIT OR Apache-2.0 OR BSD-1-Clause) AND (MIT OR Apache-2.0 OR CC0-1.0) AND (MIT OR Apache-2.0 OR LGPL-2.1-or-later) AND (MIT OR Apache-2.0 OR Zlib) AND (MIT OR Zlib OR Apache-2.0) AND MPL-2.0 AND (Unlicense OR MIT) AND Zlib AND (Zlib OR Apache-2.0 OR MIT)
URL:            https://yazi-rs.github.io/
Source0:        https://github.com/sxyazi/yazi/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  cargo-rpm-macros >= 24
BuildRequires:  mold
# compilation cache server — its cache dir lives on the workspace via the
# mock config's bind mount, shared across all rust source builds
BuildRequires:  sccache

%description
Yazi (means "duck") is a terminal file manager written in Rust, based on
non-blocking async I/O. It aims to provide an efficient, user-friendly, and
customizable file management experience, with built-in image protocols, a Lua
plugin system, async task scheduling, bulk renaming, archive extraction and
Git integration.

%prep
%autosetup
# online-cargo build config — replaces terra's %%cargo_prep_online_sccache
# (anda-srpm-macros is no longer a build input). Same shape: the [profile.rpm]
# the Fedora cargo macros build with, the redhat flag env, sccache as the
# rustc wrapper, the install root — with no [net] offline and no
# local-registry replacement, so crates fetch from crates.io at build time.
%{expand:%{!?_cargo_home:%%global _cargo_home %{rpmbuilddir}%{?buildsubdir:/%{buildsubdir}}/.cargo}}
%global __sccache %{_bindir}/sccache
mkdir -p %{_cargo_home} target/rpm
ln -s rpm target/release
cat > %{_cargo_home}/config.toml <<'EOF'
[profile.rpm]
inherits = "release"
opt-level = %{rustflags_opt_level}
codegen-units = %{rustflags_codegen_units}
debug = %{rustflags_debuginfo}
strip = "none"

[build]
rustc = "%__rustc"
rustdoc = "%__rustdoc"
rustc-wrapper = "%__sccache"

[env]
CFLAGS = "%build_cflags"
CXXFLAGS = "%build_cxxflags"
LDFLAGS = "%build_ldflags"

[install]
root = "%buildroot%{_prefix}"

[term]
verbose = true
EOF
rm -f Cargo.toml.orig
%{expand:%global __cargo /usr/bin/env CARGO_HOME=%{_cargo_home} RUSTC_BOOTSTRAP=1 RUSTFLAGS='%{build_rustflags}' /usr/bin/cargo}

%build
# cache dir on the workspace bind mount (see mock config) — survives across
# builds and is shared by every rust source build
export SCCACHE_DIR=/sccache
export VERGEN_GIT_SHA="halcyon"
%cargo_build

%install
export SCCACHE_DIR=/sccache
install -Dpm755 target/rpm/ya   %{buildroot}%{_bindir}/ya
install -Dpm755 target/rpm/yazi %{buildroot}%{_bindir}/yazi
install -Dpm644 assets/logo.png \
    %{buildroot}%{_datadir}/icons/hicolor/1024x1024/apps/yazi.png
install -Dpm644 assets/yazi.desktop \
    %{buildroot}%{_datadir}/applications/yazi.desktop
%{__cargo} tree -Z avoid-dev-deps --workspace --edges no-build,no-dev,no-proc-macro \
    --no-dedupe --target all --prefix none --format "{l}: {p}" \
    | sed -e "s: (proc-macro)::" | sort -u > LICENSE.dependencies

%files
%license LICENSE LICENSE-ICONS LICENSE.dependencies
%doc README.md CODE_OF_CONDUCT.md CONTRIBUTING.md
%{_bindir}/ya
%{_bindir}/yazi
%{_datadir}/icons/hicolor/1024x1024/apps/yazi.png
%{_datadir}/applications/yazi.desktop


%changelog
* Thu Sep 24 2026 ahsan <aahsnr041@proton.me> - 26.9.1-1
- source build with the terra cargo macro set, matching Terra's yazi.spec
  (was: prebuilt-binary wrapper over the release zip)
