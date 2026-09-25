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
BuildRequires:  anda-srpm-macros
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
%cargo_prep_online_sccache

%build
# cache dir on the workspace bind mount (see mock config) — survives across
# builds and is shared by every rust source build
export SCCACHE_DIR=/sccache
%cargo_build

%install
export SCCACHE_DIR=/sccache
install -Dpm755 target/rpm/texlab %{buildroot}%{_bindir}/texlab
%{cargo_license_online} > LICENSE.dependencies

%files
%license LICENSE LICENSE.dependencies
%doc README.md
%{_bindir}/texlab

%changelog
* Fri Sep 25 2026 halcyon-autobump <aahsnr041@proton.me>
- initial import: source build from the release tag tarball (crates.io is
  stale upstream; GH tag tarball + cargo macros per the yazi pattern)
