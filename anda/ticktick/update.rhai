// TickTick publishes no first-party version feed (the download page is
// rendered client side and the CDN serves no manifest), but the AUR package
// tracks it: the AUR maintainer bumps pkgver on every upstream release and
// the AUR RPC API exposes it. Version is pkgver-pkgrel — keep pkgver only.
let results = get_json("https://aur.archlinux.org/rpc/v5/info?arg%5B%5D=ticktick").results;
let aur_version = results[0].Version;
if aur_version == "" {
	terminate("ticktick: the AUR RPC returned no version");
}
rpm.version(sub(`-[^-]*$`, "", aur_version));
