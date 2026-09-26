# Source build: plain Makefile, libc + pthread only, no vendored deps (the
# deps/ tree is test-only frameworks).
%define debug_package %{nil}

Name:           fzy
Version:        1.1
Release:        1%{?dist}
Summary:        A simple, fast fuzzy text selector for the terminal with an advanced scoring algorithm

License:        MIT
URL:            https://github.com/jhawthorn/fzy
Source0:        %{url}/archive/refs/tags/v%{version}/fzy-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
fzy is a fuzzy text selector for the terminal: it reads lines on stdin and
prints the selected one on stdout, with a scoring algorithm that prefers
the beginning of words and consecutive matches — an alternative to pick
files, git commits, process ids and hostnames from scripts and shell key
bindings.

%prep
%autosetup -p1

%build
make PREFIX=%{_prefix} CFLAGS="%{build_cflags}"

%install
make install PREFIX=%{_prefix} DESTDIR=%{buildroot}

%files
%license LICENSE
%doc README.md
%{_bindir}/fzy
%{_mandir}/man1/fzy.1*

%changelog
* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 1.1-1
- initial packaging (source build; not packaged in Fedora)
