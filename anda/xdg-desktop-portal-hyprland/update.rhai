// Version sweeps the latest GitHub release tag of xdg-desktop-portal-hyprland
// and of sdbus-c++, whose release the bundled Source1 tarball is pinned to.
rpm.version(gh("hyprwm/xdg-desktop-portal-hyprland"));
rpm.global("sdbus_version", gh("Kistler-Group/sdbus-cpp"));
