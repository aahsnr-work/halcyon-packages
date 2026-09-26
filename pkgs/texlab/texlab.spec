# Source build following Terra's yazi.spec: the texlab workspace is NOT
# published to crates.io any more (the crates.io texlab stopped at 4.3.2 in
# 2022; upstream says to build from the git tag with --locked), so the source
# is the release tag tarball and the dependency tree is fetched over the
# network at build time (anda-srpm-macros + cargo-rpm-macros, both in
# Fedora 44). Pure-Rust dependency set: no openssl, no protoc, no C toolchain
# deps; the committed Cargo.lock keeps the build --locked-stable.
%undefine __brp_mangle_shebangs
%define debug_package %{nil}
# no debuginfo in the compiled objects either — nothing consumes it and it
# is a large share of compile time on big dependency trees
%define rustflags_debuginfo 0

Name:           texlab
Version:        5.26.0
Release:        1%{?dist}
Summary:        LaTeX Language Server Protocol implementation

# the binary itself is GPL-3.0 (upstream Cargo.toml + LICENSE); the linked
# dependency licenses are aggregated in LICENSE.dependencies
License:        GPL-3.0-only
URL:            https://github.com/latex-lsp/texlab
#!RemoteAsset
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  cargo-rpm-macros >= 24
BuildRequires:  mold
# compilation cache server — its cache dir lives on the workspace via the
# mock config's bind mount, shared across all rust source builds
BuildRequires:  sccache

%description
TeXlab is an implementation of the Language Server Protocol for LaTeX: it
provides completion, references and citations, diagnostics, formatting and
forward search for any editor with an LSP client.

%prep
%autosetup -n %{name}-%{version}
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
%cargo_build

%install
export SCCACHE_DIR=/sccache
install -Dpm755 target/rpm/texlab %{buildroot}%{_bindir}/texlab
%{__cargo} tree -Z avoid-dev-deps --workspace --edges no-build,no-dev,no-proc-macro \
    --no-dedupe --target all --prefix none --format "{l}: {p}" \
    | sed -e "s: (proc-macro)::" | sort -u > LICENSE.dependencies

%files
%license LICENSE LICENSE.dependencies
%doc README.md
%{_bindir}/texlab

%changelog
* Fri Sep 25 2026 ahsan <aahsnr041@proton.me> - 5.26.0-1
- initial import: source build from the release tag tarball (crates.io is
  stale upstream; GH tag tarball + cargo macros per the yazi pattern)
