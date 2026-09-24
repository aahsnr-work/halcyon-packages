// noctalia-git tracks the noctalia-dev/noctalia branch tip, not a release:
// the spec pins the commit in a %global and keeps the last tag as the version
// base with a ^N snapshot counter — a new commit under the same tag bumps the
// counter, a new tag resets it. Ported from the old fetch.sh; the Release:
// line is left alone.
let repo = "noctalia-dev/noctalia";
let spec = "noctalia-git.spec";
let dir = sub(`/[^/]+$`, "", __script_path);

let old_commit = find(`(?m)^%global[ \t]+commit[ \t]+(\S+)`, rpm.get(), 1);
let new_commit = gh_commit(repo);
// old_version as rpmdev sees it (the Version line carries %{shortcommit})
let old_version = sub(`\s`, "", sh(`rpmspec -q --qf '%{version}' ` + dir + `/` + spec, #{}).ctx.stdout);
let old_base = sub(`\^.*`, "", old_version);
let tag_raw = gh_tag(repo);
let new_tag = if tag_raw == "" || tag_raw == "null" { old_base } else { sub(`-`, `~`, tag_raw) };

let ec = sh("rpmdev-vercmp '" + old_version + "' '" + new_tag + "'", #{}).ctx.rc;

if old_commit != new_commit || ec == 12 {
	if ec == 12 {
		// newer tag: reset the snapshot counter
		rpm.set(sub(`(?m)^Version:[ \t]*\S+`,
			`Version:\t` + new_tag + `^1.%{shortcommit}`, rpm.get()));
	} else {
		// same version base: bump the snapshot counter
		let n;
		try {
			n = find(`(?m)^Version:[ \t]*[^ \t]*\^(\d+)`, rpm.get(), 1).parse_int() + 1;
		} catch {
			n = 1;
		}
		rpm.set(sub(`(?m)^Version:[ \t]*\S+`,
			`Version:\t` + old_base + `^` + n + `.%{shortcommit}`, rpm.get()));
	}
	rpm.global("commit", new_commit);
}
