# Data package: all 32 static TTFs from the upstream release zip's
# fonts/ttf — the full "JetBrains Mono" family and the no-ligatures
# "JetBrains Mono NL" family, every weight and style (upstream ships no
# Windows-compatible duplicates). The zip's variable/otf/webfonts are not
# installed: the static set is what fontconfig serves for both families.
Name:           jetbrains-mono-fonts-all
Version:        2.304
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        JetBrains Mono developer font — all weights of Mono and Mono NL
BuildArch:      noarch
License:        OFL-1.1
URL:            https://www.jetbrains.com/lp/mono/
Source0:        https://github.com/JetBrains/JetBrainsMono/releases/download/v%{version}/JetBrainsMono-%{version}.zip

BuildRequires:  unzip

%description
JetBrains Mono is a monospaced font tuned for developers (increased
character height for code readability, ligatures, 145+ languages). This
package installs every static weight and style of both shipped families —
"JetBrains Mono" and the no-ligatures "JetBrains Mono NL".

%prep
%setup -q -c

%install
mkdir -p %{buildroot}%{_datadir}/fonts/jetbrains-mono
install -m644 -t %{buildroot}%{_datadir}/fonts/jetbrains-mono fonts/ttf/*.ttf

%files
%{_datadir}/fonts/jetbrains-mono/
%license OFL.txt

%changelog
* Mon Sep 28 2026 halcyon-autoupdate <aahsnr041@proton.me> - 2.304-1
- initial packaging: all static weights of JetBrains Mono and JetBrains Mono NL
