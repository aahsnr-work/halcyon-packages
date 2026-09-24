# Wrapper over bat's official prebuilt x86_64-gnu release tarball (Arch-
# PKGBUILD style; upstream ships no rpm). mock fetches the tarball at SRPM
# build time (anda enables network for URL sources), %prep only unpacks it.
# The tarball ships the man page, shell completions and the MIT license —
# all installed.
Name:           bat
Version:        0.26.1
Release:        1%{?dist}
Summary:        A cat(1) clone with syntax highlighting and Git integration
License:        MIT OR Apache-2.0
URL:            https://github.com/sharkdp/bat
Source0:        %{url}/releases/download/v%{version}/bat-v%{version}-x86_64-unknown-linux-gnu.tar.gz

ExclusiveArch:  x86_64

%description
bat is a cat(1) clone with syntax highlighting, Git integration, automatic
paging and a user-friendly command-line interface.

%prep
%autosetup -n bat-v%{version}-x86_64-unknown-linux-gnu

%install
install -Dpm755 bat %{buildroot}%{_bindir}/bat
install -Dpm644 bat.1 %{buildroot}%{_mandir}/man1/bat.1
install -Dpm644 completions/bat.bash \
    %{buildroot}%{_datadir}/bash-completion/completions/bat
install -Dpm644 completions/bat.zsh \
    %{buildroot}%{_datadir}/zsh/site-functions/_bat
install -Dpm644 completions/bat.fish \
    %{buildroot}%{_datadir}/fish/vendor_completions.d/bat.fish

%files
%license LICENSE-MIT
%{_bindir}/bat
%{_mandir}/man1/bat.1*
%{_datadir}/bash-completion/completions/bat
%{_datadir}/zsh/site-functions/_bat
%{_datadir}/fish/vendor_completions.d/bat.fish
