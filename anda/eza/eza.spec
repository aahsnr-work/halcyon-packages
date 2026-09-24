# Wrapper over eza's official prebuilt x86_64-gnu release (Arch-PKGBUILD
# style; upstream ships no rpm). Upstream splits the release into three
# tarballs: the binary, the man pages and the shell completions — all three
are fetched by mock at SRPM-build time and installed here.
Name:           eza
Version:        0.23.5
Release:        1%{?dist}
Summary:        A modern, maintained replacement for ls
License:        MIT
URL:            https://eza.rocks
Source0:        https://github.com/eza-community/eza/releases/download/v%{version}/eza_x86_64-unknown-linux-gnu.tar.gz
Source1:        https://github.com/eza-community/eza/releases/download/v%{version}/man-%{version}.tar.gz
Source2:        https://github.com/eza-community/eza/releases/download/v%{version}/completions-%{version}.tar.gz

ExclusiveArch:  x86_64

%description
eza is a modern replacement for ls, with file icons, Git integration and
tree views.

%prep
%setup -q -c -T
tar -xf %{_sourcedir}/eza_x86_64-unknown-linux-gnu.tar.gz
tar -xf %{_sourcedir}/man-%{version}.tar.gz
tar -xf %{_sourcedir}/completions-%{version}.tar.gz

%install
install -Dpm755 eza %{buildroot}%{_bindir}/eza
install -Dpm644 target/man-%{version}/eza.1 %{buildroot}%{_mandir}/man1/eza.1
install -Dpm644 target/man-%{version}/eza_colors.5 \
    %{buildroot}%{_mandir}/man5/eza_colors.5
install -Dpm644 target/completions-%{version}/eza \
    %{buildroot}%{_datadir}/bash-completion/completions/eza
install -Dpm644 target/completions-%{version}/_eza \
    %{buildroot}%{_datadir}/zsh/site-functions/_eza
install -Dpm644 target/completions-%{version}/eza.fish \
    %{buildroot}%{_datadir}/fish/vendor_completions.d/eza.fish

%files
%{_bindir}/eza
%{_mandir}/man1/eza.1*
%{_mandir}/man5/eza_colors.5*
%{_datadir}/bash-completion/completions/eza
%{_datadir}/zsh/site-functions/_eza
%{_datadir}/fish/vendor_completions.d/eza.fish
