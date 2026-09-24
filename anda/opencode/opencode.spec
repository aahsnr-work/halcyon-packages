# Ported to opencode's v2 line (2.0.x — the major rewrite). Upstream ships no
# rpm; the v2 install script resolves the version from
# https://opencode.ai/update/api/latest/cli/npm and installs the binary from
# the npm package @opencode/cli-linux-x64 (single executable at package/bin/
# opencode). The same npm tarball is repackaged here — Source0 is pinned to
# the @opencode scope; update.rhai resolves the scope dynamically in case
# upstream moves it (like the legacy @opencode-ai one).
Name:           opencode
Version:        2.0.14
Release:        5%{?dist}
Summary:        AI coding agent for the terminal
License:        MIT
URL:            https://opencode.ai
Source0:        https://registry.npmjs.org/@opencode%2Fcli-linux-x64/-/cli-linux-x64-%{version}.tgz
BuildArch:      x86_64
%description
AI coding agent built for the terminal, from the upstream v2 release binary.
%prep
%setup -q -c -T
# tarball is provided at SRPM-build time, never downloaded in %prep.
tar -xzf %{_sourcedir}/cli-linux-x64-%{version}.tgz
%install
install -Dm0755 package/bin/opencode %{buildroot}%{_bindir}/opencode
%files
%{_bindir}/opencode
%changelog
* Mon Sep 22 2026 halcyon-autobuild - 2.0.14-5
- follow the v2 line (major rewrite): the version now sweeps
  opencode.ai/update/api/latest/cli/npm and the binary comes from the
  @opencode/cli-linux-x64 npm package (the old v1 GitHub-release zip asset
  no longer tracks the current version)
* Mon Sep 22 2026 halcyon-autobuild - 1.18.31-4
- follow the current release artifact: opencode-linux-x64.tar.gz (the
  opencode-linux-x64.zip asset of the 0.12.0 era is gone upstream) and
  un-tar in %prep instead of unzip; latest release is 1.18.31
- drop %%license (the archive contains only the opencode binary) and the
  unused curl/unzip BuildRequires
* Mon Sep 21 2026 halcyon-autobuild - 0.12.0-3
- take the release zip from the source directory instead of curl in %prep
  (Copr builds have no network; the source method script ships the file)
* Mon Sep 21 2026 halcyon-autobuild - 0.12.0-2
- fix upstream repo: sst/opencode was renamed to anomalyco/opencode
- fix release asset name: opencode-linux-x64.zip, not opencode-linux-x86_64.zip
- add missing BuildRequires: curl, unzip (used in %prep but never declared)
