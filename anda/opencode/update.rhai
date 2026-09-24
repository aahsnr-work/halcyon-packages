// Version sweeps opencode.ai's own update API (the v2 line ships through it,
// not through GitHub releases). The npm scope that carries the version's
// cli-linux-x64 tarball is resolved from the same endpoint — older versions
// only exist under the legacy @opencode-ai scope — and Source0 is rewritten
// when the scope moves.
let meta = get("https://opencode.ai/update/api/latest/cli/npm");
rpm.version(find(`"version":"([^"]+)"`, meta, 1));
let scope = "@opencode";
try {
	scope = sub(`/cli$`, "", find(`"package":"([^"]*)/cli"`, meta, 1));
} catch {
	// endpoint answered without a package field — keep the pinned scope
}
if scope != "@opencode" {
	rpm.source(0, "https://registry.npmjs.org/" + scope + "%2Fcli-linux-x64/-/cli-linux-x64-%{version}.tgz");
}
