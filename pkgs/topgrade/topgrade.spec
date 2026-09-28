# Written for halcyon-packages (rust2rpm-style, bin crate); ported from
# li-lay/topgrade-watcher's Copr-tracking spec (their watcher sweeps the same
# topgrade-rs/topgrade releases and builds on the same crates.io tag).
# Sources: the crates.io URL is spelled out — the CI submit job fetches it
# with spectool at SRPM-build time; keep downloads out of the prep stage.
# Registration: ci/packages.toml (batch + [pkg.updates] feed).
%undefine __brp_mangle_shebangs
%define debug_package %{nil}
# no debuginfo in the compiled objects either — nothing consumes it and it
# is a large share of compile time on big dependency trees
%define rustflags_debuginfo 0
%bcond check 0

%global crate topgrade

Name:           topgrade
Version:        17.12.2
Release:        1%{?dist}
Summary:        Upgrade all the things

License:        GPL-3.0-or-later
URL:            https://crates.io/crates/topgrade
Source0:        https://static.crates.io/crates/%{crate}/%{crate}-%{version}.crate

BuildRequires:  cargo-rpm-macros >= 24
BuildRequires:  sccache

%description
Topgrade is a tool that keeps your system up to date by invoking multiple
package managers. It detects which tools you use and runs the appropriate
commands to update them.

%files
%license LICENSE
%license LICENSE.dependencies
%doc README.md
%{_bindir}/topgrade

%prep
%autosetup -n %{crate}-%{version} -p1
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
export SCCACHE_DIR=/sccache
%{__cargo} tree -Z avoid-dev-deps --workspace --edges no-build,no-dev,no-proc-macro \
    --no-dedupe --target all --prefix none --format "{l}: {p}" \
    | sed -e "s: (proc-macro)::" | sort -u > LICENSE.dependencies

%install
export SCCACHE_DIR=/sccache
%cargo_install -- --locked

%if %{with check}
%check
%cargo_test
%endif

%changelog
* Mon Sep 28 2026 ahsan <aahsnr041@proton.me> - 17.12.2-1
- initial packaging (rust source build; ported from li-lay/topgrade-watcher)
