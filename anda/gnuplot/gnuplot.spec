# Source build of gnuplot from the official SourceForge tarball — kept in
# this repo even though Fedora carries gnuplot, per the halcyon requirement
# that these packages install from this repository. Build is a lean console/
# cairo/png/svg configuration (--without-qt --without-wx): the image uses
# gnuplot for non-interactive PNG/SVG output; add qt5-qtbase-devel and drop
# the --without-qt flag if an interactive qt terminal is ever needed.
Name:           gnuplot
Version:        6.0.5
Release:        1%{?dist}
Summary:        Program for plotting functions and data
License:        gnuplot
URL:            http://gnuplot.info
Source0:        https://downloads.sourceforge.net/project/gnuplot/gnuplot/%{version}/gnuplot-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libpng-devel
BuildRequires:  libjpeg-turbo-devel
BuildRequires:  zlib-devel
BuildRequires:  cairo-devel
BuildRequires:  pango-devel
BuildRequires:  gd-devel
BuildRequires:  lua-devel
BuildRequires:  libX11-devel
BuildRequires:  libcerf-devel

%description
Gnuplot is a portable command-line driven graphing utility for Linux, OS/2,
MS Windows, OSX, VMS, and many other platforms. This build provides the
cairo (pngcairo/pdfcairo/svg), png/jpeg/gif, lua and x11 terminals.

%prep
%autosetup -p1

%build
%configure --without-qt --without-wx
%make_build

%install
%make_install
rm -f %{buildroot}%{_libdir}/libgnuplot.la

%files
%{_bindir}/gnuplot
%{_mandir}/man1/gnuplot.1*
%{_datadir}/gnuplot/

%changelog
* Mon Sep 22 2026 halcyon-autobuild - 6.0.5-1
- lean console/cairo build kept in the halcyon repository
