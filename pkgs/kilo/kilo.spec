# The release tarball is a multi-file tree, not a single binary: the main
# executable needs its sandbox helpers (bwrap + seccomp), the console web
# UI and the tree-sitter WASM grammars as siblings — all installed under
# /usr/lib/kilo with a wrapper that pins the grammar directory.
%define debug_package %{nil}
%global _build_id_links none

Name:           kilo
Version:        7.8.1
Release:        1%{?dist}
Summary:        The AI coding agent built for the terminal

License:        MIT AND LGPL-2.0-or-later
URL:            https://github.com/Kilo-Org/kilocode
Source0:        %{url}/releases/download/v%{version}/kilo-linux-x64.tar.gz
#!RemoteAsset
ExclusiveArch:  x86_64

Requires:       ripgrep

%description
Kilo is an AI coding agent for the terminal: it plans, edits and runs code
across a workspace, with sandboxed command execution (bundled bubblewrap),
a built-in web console and tree-sitter grammars for its code intelligence.

%prep
%autosetup -n %{name} -c

%build
# prebuilt upstream tree

%install
install -d %{buildroot}%{_libdir}/%{name} %{buildroot}%{_bindir}
install -pm0755 kilo %{buildroot}%{_libdir}/%{name}/kilo
install -pm0755 bwrap %{buildroot}%{_libdir}/%{name}/bwrap
install -pm0644 kilo-sandbox-mutation-worker.js %{buildroot}%{_libdir}/%{name}/
cp -a tree-sitter %{buildroot}%{_libdir}/%{name}/tree-sitter
# the wrapper pins the grammar dir; the sandbox helpers are resolved
# relative to the real binary
cat > %{buildroot}%{_bindir}/kilo <<'EOF'
#!/bin/sh
export KILO_TREE_SITTER_WASM_DIR=%{_libdir}/%{name}/tree-sitter
exec %{_libdir}/%{name}/kilo "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/kilo
install -d %{buildroot}%{_licensedir}/%{name}
cp -a licenses/. %{buildroot}%{_licensedir}/%{name}/

%files
%license %{_licensedir}/%{name}/
%{_bindir}/kilo
%{_libdir}/%{name}/

%changelog
* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 7.8.1-1
- initial packaging (release-tree wrapper per the kilo-bin AUR pattern;
  the GitHub release feed is polluted by jetbrains tags, so the sweep
  tracks the npm dist-tag)
