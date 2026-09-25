// Version sweeps the newest obsidianmd/obsidian-releases release that ships
// the desktop linux tarball (obsidian-<version>.tar.gz asset); the release's
# the release's sha256 asset digest is pinned in %%global digest for the
# %prep checksum (the 'none' sentinel skips the check when upstream
# publishes no digest)
// (empty when upstream publishes none — the check then skips itself).
// GitHub orders releases newest-first, so the first asset match is current.
let text = get("https://api.github.com/repos/obsidianmd/obsidian-releases/releases?per_page=30");
rpm.version(find(`"name":"obsidian-([0-9.]+)\.tar\.gz"`, text, 1));
try {
	rpm.global("digest", find(
		`(?s)"name":"obsidian-[0-9.]+\.tar\.gz".*?"digest":"sha256:([0-9a-f]{64})"`,
		text, 1));
} catch {
	rpm.global("digest", "none");
}
