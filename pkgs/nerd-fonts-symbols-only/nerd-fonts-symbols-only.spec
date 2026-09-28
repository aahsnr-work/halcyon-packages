Name:           nerd-fonts-symbols-only
Version:        3.5.1
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        Symbols-only Nerd Font with icon glyphs for fallback use
BuildArch:      noarch

License:        MIT
URL:            https://github.com/ryanoasis/nerd-fonts
Source0:        https://github.com/ryanoasis/nerd-fonts/releases/download/v%{version}/NerdFontsSymbolsOnly.tar.xz
Source1:        https://raw.githubusercontent.com/ryanoasis/nerd-fonts/v%{version}/10-nerd-font-symbols.conf

%description
Nerd Fonts patches developer-targeted fonts with a high number of extra
glyphs (icons) from popular iconic fonts such as Font Awesome, Devicons,
Octicons, and others. This package contains the symbols-only fallback
font, which provides the Nerd Font glyph set without patching a base
font, plus the fontconfig rules that make other fonts fall back to it
for missing glyphs.


%prep
%setup -c -q
# upstream ships Windows-named duplicate variants alongside the standard
# files; drop them so only the standard ttf payload is installed
find . -name '* Windows Compatible*' -type f -delete


%install
mkdir -p %{buildroot}%{_datadir}/fonts/nerd-fonts/NerdFontsSymbolsOnly
install -m644 -t %{buildroot}%{_datadir}/fonts/nerd-fonts/NerdFontsSymbolsOnly *.ttf
install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/fontconfig/conf.avail/10-nerd-font-symbols.conf
mkdir -p %{buildroot}%{_sysconfdir}/fonts/conf.d
ln -s %{_datadir}/fontconfig/conf.avail/10-nerd-font-symbols.conf %{buildroot}%{_sysconfdir}/fonts/conf.d/10-nerd-font-symbols.conf


%files
%{_datadir}/fonts/nerd-fonts/NerdFontsSymbolsOnly/
%{_datadir}/fontconfig/conf.avail/10-nerd-font-symbols.conf
%{_sysconfdir}/fonts/conf.d/10-nerd-font-symbols.conf
%license LICENSE
%doc README.md


%changelog
* Mon Sep 28 2026 ahsan <aahsnr041@proton.me> - 3.5.1-1
- initial package
