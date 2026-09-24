// Version sweeps the latest git tag of hyprland-community/pyprland (tags are cut without
// GitHub releases; rpm.version strips the leading v itself).
rpm.version(gh_tag("hyprland-community/pyprland"));
