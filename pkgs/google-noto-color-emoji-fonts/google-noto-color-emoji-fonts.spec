# Vendor install of the current Noto Color Emoji font from google/fonts
# (ofl/notocoloremoji) pinned to the commit that last touched the file —
# googlefonts/noto-emoji attaches no font assets to its releases and its
# tag trees carry no built font, while google/fonts distributes the
# official COLRv1 build (the 3.x redesign; Unicode 18.0 era). Version is
# the pinned commit's date, maintained by custom_noto_color_emoji in
# ci/sweep/custom.py, which also rewrites the noto_commit global.
%global noto_commit 142c8963e760
Name:           google-noto-color-emoji-fonts
Version:        20260909
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        Noto Color Emoji — Google's color emoji font (COLRv1)
BuildArch:      noarch
License:        OFL-1.1
URL:            https://github.com/googlefonts/noto-emoji
Source0:        https://raw.githubusercontent.com/google/fonts/%{noto_commit}/ofl/notocoloremoji/NotoColorEmoji-Regular.ttf
Source1:        https://raw.githubusercontent.com/google/fonts/%{noto_commit}/ofl/notocoloremoji/OFL.txt

%description
Noto Color Emoji is Google's emoji font covering the full Unicode emoji
set — the reference emoji font for Linux desktops, here the COLRv1 vector
build of the 3.x redesign. Provides the "emoji" family that fontconfig
resolves for emoji fallback.

%prep
%setup -T -c
cp %{SOURCE1} OFL.txt

%install
install -Dm644 %{SOURCE0} %{buildroot}%{_datadir}/fonts/google-noto-color-emoji/NotoColorEmoji.ttf

%files
%{_datadir}/fonts/google-noto-color-emoji/
%license OFL.txt

%changelog
* Mon Sep 28 2026 halcyon-autoupdate <aahsnr041@proton.me> - 20260909-1
- initial packaging: google/fonts COLRv1 build pinned to commit 142c8963e760
