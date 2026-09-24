# Wrapper over tealdeer's official prebuilt musl release binary (single
# static executable) plus its release-published shell completion files.
Name:           tealdeer
Version:        1.9.0
Release:        1%{?dist}
Summary:        A fast tldr client in Rust
License:        MIT OR Apache-2.0
URL:            https://tealdeer-rs.github.io/tealdeer/
%global url_base https://github.com/dbrgn/tealdeer
Source0:        %{url_base}/releases/download/v%{version}/tealdeer-linux-x86_64-musl
Source1:        %{url_base}/releases/download/v%{version}/completions_bash
Source2:        %{url_base}/releases/download/v%{version}/completions_fish
Source3:        %{url_base}/releases/download/v%{version}/completions_zsh

ExclusiveArch:  x86_64

%description
Tealdeer is a fast tldr client: community-driven example pages for command
line tools, cached locally for offline use.

%prep
%setup -q -c -T
# nothing to unpack — the sources are a bare binary and bare completion files

%install
install -Dpm755 %{SOURCE0} %{buildroot}%{_bindir}/tealdeer
install -Dpm644 %{SOURCE1} %{buildroot}%{_datadir}/bash-completion/completions/tldr
install -Dpm644 %{SOURCE3} %{buildroot}%{_datadir}/zsh/site-functions/_tldr
install -Dpm644 %{SOURCE2} %{buildroot}%{_datadir}/fish/vendor_completions.d/tldr.fish

%files
%{_bindir}/tealdeer
%{_datadir}/bash-completion/completions/tldr
%{_datadir}/zsh/site-functions/_tldr
%{_datadir}/fish/vendor_completions.d/tldr.fish
