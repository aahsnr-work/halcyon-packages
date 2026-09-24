# Wrapper over atuin's official prebuilt x86_64-gnu release tarball (Arch-
# PKGBUILD style; upstream ships no rpm). mock fetches the tarball at SRPM
# build time (anda enables network for URL sources), %prep only unpacks it.
Name:           atuin
Version:        18.22.0
Release:        1%{?dist}
Summary:        Synced, searchable shell history with onboard encryption
License:        MIT
URL:            https://atuin.sh
Source0:        https://github.com/atuinsh/atuin/releases/download/v%{version}/atuin-x86_64-unknown-linux-gnu.tar.gz

ExclusiveArch:  x86_64

%description
Atuin replaces your existing shell history with a SQLite database, and logs
additional context for commands. Entirely optional, self-hosted sync server;
history is encrypted end to end.

%prep
%autosetup -n atuin-x86_64-unknown-linux-gnu

%install
install -Dpm755 atuin %{buildroot}%{_bindir}/atuin

%files
%doc CHANGELOG.md
%{_bindir}/atuin
