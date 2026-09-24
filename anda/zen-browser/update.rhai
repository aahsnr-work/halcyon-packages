// Version sweeps the latest GitHub release tag of zen-browser/desktop
// (ported from Terra's update.rhai):
//   * rpm.global("download_ver", tag) — the download URL keeps the tag,
//     channel letter included
//   * the spec Version drops the trailing channel letter (only when the tag
//     actually ends in one — same result for every real zen tag)
let v = gh("zen-browser/desktop");
rpm.global("download_ver", v);
if find(`[a-zA-Z]$`, v, 0) != "" {
	v.truncate(v.len - 1);
}
rpm.version(v);
