Name:           lazygit
Version:	0.65.1
Release:        1%{?dist}
Summary:        Simple terminal UI for git commands
License:        MIT
URL:            https://github.com/jesseduffield/lazygit
Source0:        %{url}/releases/download/v%{version}/lazygit_%{version}_Linux_x86_64.tar.gz
BuildArch:      x86_64
BuildRequires:  curl
%description
A simple terminal UI for git commands, built from the upstream release binary.
%prep
%setup -q -c -T -a 0
%define debug_package %{nil}
%install
install -Dm0755 lazygit %{buildroot}%{_bindir}/lazygit
%files
%{_bindir}/lazygit
%changelog
* Sat Sep 19 2026 halcyon-autobuild - 0.65.1-1
- packaged from upstream release binary
