Name:           nerd-fonts-ubuntu
Version:        3.5.1
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        Ubuntu patched with Nerd Fonts icons
BuildArch:      noarch

License:        Ubuntu-Font-1.0
URL:            https://github.com/ryanoasis/nerd-fonts
Source0:        https://github.com/ryanoasis/nerd-fonts/releases/download/v%{version}/Ubuntu.tar.xz

%description
Nerd Fonts patches developer-targeted fonts with a high number of extra
glyphs (icons) from popular iconic fonts such as Font Awesome, Devicons,
Octicons, and others. This package contains the patched version of the
Ubuntu font family (regular, mono and propo variants).


%prep
%setup -c -q
# upstream ships Windows-named duplicate variants alongside the standard
# files; drop them so only the standard ttf payload is installed
find . -name '* Windows Compatible*' -type f -delete


%install
mkdir -p %{buildroot}%{_datadir}/fonts/nerd-fonts/Ubuntu
install -m644 -t %{buildroot}%{_datadir}/fonts/nerd-fonts/Ubuntu *.ttf


%files
%{_datadir}/fonts/nerd-fonts/Ubuntu/
%license LICENCE.txt LICENCE-FAQ.txt
%doc README.md


%changelog
* Mon Sep 28 2026 ahsan <aahsnr041@proton.me> - 3.5.1-1
- initial package
