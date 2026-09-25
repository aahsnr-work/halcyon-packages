# Ported from terrapkg/packages frawhide (anda/tools/chafa) on 2026-09-22 and
# adapted to this repo's Copr custom-source pipeline. Deviations from upstream:
#   * Name drops the terra- prefix (that is Terra's repo-wide convention for
#     packages that also exist in Fedora; there is no clash to avoid here).
#   * %pkg_libs_files / %pkg_devel_files / %pkg_static_files are
#     anda-srpm-macros auto-file-lists — replaced with explicit %files lists.
#   * %{evr} (an anda macro) -> %{version}-%{release}.
#   * the .la removal is unconditional (the %if 0%{?rhel} guard never fires on
#     Fedora, and an unpacked .la would fail the build).
# The source tarball is fetched by mock at SRPM-build time (this repo keeps
# downloads out of %prep; anda enables network for URL sources).
Name:           chafa
Version:        1.18.2
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        Terminal graphics for the 21st century
License:        LGPL-3.0-or-later AND GPL-3.0-or-later
URL:            https://hpjansson.org/chafa/
#!RemoteAsset
Source0:        https://github.com/hpjansson/chafa/archive/refs/tags/%version.tar.gz

BuildRequires:  gcc
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  gettext-devel
BuildRequires:  gtk-doc
BuildRequires:  libtool
BuildRequires:  make
BuildRequires:  libjpeg-turbo-devel
BuildRequires:  libavif-devel
BuildRequires:  librsvg2-devel
BuildRequires:  libtiff-devel
BuildRequires:  libwebp-devel
BuildRequires:  libpng-devel
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

Packager:       Owen Zimmerman <owen@fyralabs.com>

%description
Chafa is a command-line utility that converts all kinds of images, including
animated image formats like GIFs, into ANSI/Unicode character output that can
be displayed in a terminal.

It is highly configurable, with support for alpha transparency and multiple
color modes and color spaces, combining a range of Unicode characters for
optimal output.

%package libs
Summary:        Libraries for chafa
%description libs
Libraries for chafa.

%package devel
Summary:        Development files for chafa
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
%description devel
Development files for chafa.

%package static
Summary:        Static libraries for chafa
Requires:       %{name}-devel%{?_isa} = %{version}-%{release}
%description static
Static libraries for chafa.

%prep
%autosetup -n chafa-%{version}

%conf
autoreconf -ivf
%configure --disable-rpath

%build
%make_build

%install
%make_install
find %{buildroot} -name "*.la" -delete

# upstream: %pkg_libs_files
%files libs
%license COPYING.LESSER COPYING
%{_libdir}/libchafa.so.*

# upstream: %pkg_devel_files
%files devel
%doc AUTHORS NEWS README*
%{_includedir}/chafa/
%{_libdir}/libchafa.so
%{_libdir}/pkgconfig/chafa.pc
%{_libdir}/chafa/include/chafaconfig.h

# upstream: %pkg_static_files
%files static
%{_libdir}/libchafa.a

%files
%doc AUTHORS COPYING.LESSER README* NEWS
%license COPYING.LESSER COPYING
%{_bindir}/chafa
%{_mandir}/man1/chafa.1*

%changelog
* Fri Feb 20 2026 Owen Zimmerman <owen@fyralabs.com>
- Initial commit
