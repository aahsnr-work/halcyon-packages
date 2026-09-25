# Ported from terrapkg/packages frawhide (anda/devs/bun) on 2026-09-22 and
# adapted to this repo's Copr custom-source pipeline. Deviations from upstream:
#   * anda-srpm-macros / terra-appstream-helper are Terra build-env packages —
#     removed; %pkg_completion and %terra_appstream are Terra macros, replaced
#     with the explicit Fedora equivalents (marked inline). The shell
#     completion files land in the main package instead of %pkg_completion's
#     generated subpackages.
#   * The release zip is fetched by mock at SRPM-build time (anda enables
#     network for URL sources; %prep never downloads anything itself); the
#     spec is otherwise upstream verbatim.
%define debug_package %nil
%ifarch x86_64
%global a x64-baseline
%elifarch aarch64
%global a aarch64
%endif

%global appid sh.oven.bun
%global bash_completions_dir %{_datadir}/bash-completion/completions
%global zsh_completions_dir %{_datadir}/zsh/site-functions
%global fish_completions_dir %{_datadir}/fish/vendor_completions.d

Name:		bun
Version:		1.4.2
Release:		1%{?dist}
Summary:		Incredibly fast JavaScript runtime, bundler, test runner, and package manager – all in one
License:		MIT
URL:			https://bun.sh
#!RemoteAsset
Source0:		https://github.com/oven-sh/bun/releases/download/bun-v%version/bun-linux-%a.zip
Source1:		sh.oven.bun.metainfo.xml
BuildRequires:	unzip

%description
%summary.

%prep
%autosetup -n bun-linux-%a
cat<<EOF > LICENSE
MIT License

Copyright (c) Jarred Sumner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

%install
declare -a shells=("zsh" "bash" "fish")
for s in "${shells[@]}"; do
	SHELL=$s ./bun completions > bun.$s
done

install -Dpm755 bun -t %buildroot%_bindir
install -Dm644 bun.zsh %buildroot%zsh_completions_dir/_bun
install -Dm644 bun.bash %{buildroot}%bash_completions_dir/bun
install -Dm644 bun.fish -t %buildroot%fish_completions_dir
ln -s bun %buildroot%_bindir/bunx

# upstream: %terra_appstream -o %{SOURCE1}
install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/metainfo/sh.oven.bun.metainfo.xml

# upstream: %pkg_completion -bfz bun (generated its own completion subpackages;
# the files are kept in the main package here)
%files
%license LICENSE
%_bindir/bun
%_bindir/bunx
%{_datadir}/metainfo/sh.oven.bun.metainfo.xml
%{_datadir}/bash-completion/completions/bun
%{_datadir}/zsh/site-functions/_bun
%{_datadir}/fish/vendor_completions.d/bun.fish
