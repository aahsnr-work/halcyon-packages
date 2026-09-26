# Upstream ships bare self-contained .NET release binaries (no crates.io
# publish — the crates.io "marksman" name is an unrelated squatter, no RPM,
# not in Fedora), so the wrapper follows the tealdeer/opencode shape: the
# release binary as Source0, the repo LICENSE as Source1 (release assets
# carry no license text). Tags are dates (2026-02-08); the version converts
# the dashes to dots and the raw tag travels in %%markstag for the URLs.
%define debug_package %{nil}

%global markstag 2026-02-08

Name:           marksman
Version:        2026.02.08
Release:        1%{?dist}
Summary:        Markdown LSP server providing completion, goto and diagnostics

License:        MIT
URL:            https://github.com/artempyanykh/marksman
#!RemoteAsset
Source0:        %{url}/releases/download/%{markstag}/marksman-linux-x64
#!RemoteAsset
Source1:        %{url}/raw/%{markstag}/LICENSE

ExclusiveArch:  x86_64

# self-contained .NET dlopens ICU for globalization; not visible in
# DT_NEEDED, so the dependency generator cannot see it
Requires:       libicu

%description
Marksman is a Markdown language server: completion, goto-definition,
signature help, references, diagnostics and cross-file linking for your
editor's LSP client.

%prep
# nothing to unpack — Source0 is the binary itself
cp -p %{SOURCE0} marksman

%build
# nothing to compile: the upstream binary ships as-is

%install
install -Dpm755 marksman %{buildroot}%{_bindir}/marksman
install -Dpm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%license %{_licensedir}/%{name}/LICENSE
%{_bindir}/marksman

%changelog
* Fri Sep 25 2026 halcyon-autobump <aahsnr041@proton.me>
- initial import: wrapper over the upstream linux-x64 release binary
  (date-tag version converted to dots for RPM)
