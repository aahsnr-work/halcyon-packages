// hyprland-git tracks the Hyprland main-branch tip rather than a release:
// the spec records the commit, its commit date, the total commit count and
// the SHAs of the bundled hyprland-protocols / udis86 submodule trees. Every
// one of those is refreshed here; a changed revision bumps the bumpver
// snapshot counter, and a new upstream tag resets it first. Ported from the
// old fetch.sh.
let repo = "hyprwm/Hyprland";

let old_base = find(`(?m)^Version:[ \t]*([0-9.]+)`, rpm.get(), 1);
let new_tag = gh_tag(repo);
let old_commit = find(`(?m)^%global[ \t]+hyprland_commit[ \t]+(\S+)`, rpm.get(), 1);
let new_commit = gh_commit(repo);

// total commits on main: the old fetcher read the Link header of a
// per_page=1 listing (last page number == total commits) — andax's get()
// cannot see headers, so curl reads them.
let gh_auth = if env("GITHUB_TOKEN") != "" {
	["-H", "Authorization: Bearer " + env("GITHUB_TOKEN")]
} else {
	[]
};
let new_commits = sub(`\s`, "", sh(
	["curl", "-fsSI", "-H", "Accept: application/vnd.github+json"] + gh_auth +
		["https://api.github.com/repos/" + repo + "/commits?per_page=1&sha=" + new_commit],
	#{}).ctx.stdout);
let new_commits = find(`(?i)link:.*"next".*page=([0-9]+).*"last"`, new_commits, 1);

let old_date = find(`(?m)^%global[ \t]+commit_date[ \t]+(.+?)\n`, rpm.get(), 1);
let new_date = sub(`\n`, "", sh([
	"date", "-d", get_json("https://api.github.com/repos/" + repo + "/commits/" + new_commit)
		.commit.author.date, "+%a %b %d %T %Y",
], #{}).ctx.stdout);

let old_protocols = find(`(?m)^%global[ \t]+protocols_commit[ \t]+(\S+)`, rpm.get(), 1);
let new_protocols = get_json(
	"https://api.github.com/repos/" + repo + "/contents/subprojects/hyprland-protocols?ref=" + new_commit
).sha;
let old_udis86 = find(`(?m)^%global[ \t]+udis86_commit[ \t]+(\S+)`, rpm.get(), 1);
let new_udis86 = get_json(
	"https://api.github.com/repos/" + repo + "/contents/subprojects/udis86?ref=" + new_commit
).sha;

for value in [new_tag, new_commit, new_commits, new_date, new_protocols, new_udis86] {
	if value == "" {
		terminate("hyprland-git: empty value from the GitHub API");
	}
}

// pin the new revisions (rpm.global rewrites the %global line and leaves the
// %-macro indirections like hyprland_shortcommit intact)
rpm.global("commits_count", new_commits);
if old_date != new_date {
	rpm.set(sub(old_date, new_date, rpm.get()));
}
if old_commit != new_commit {
	rpm.global("hyprland_commit", new_commit);
}
if old_protocols != new_protocols {
	rpm.global("protocols_commit", new_protocols);
}
if old_udis86 != new_udis86 {
	rpm.global("udis86_commit", new_udis86);
}

// snapshot counter: a new upstream tag resets it first (rpmdev-vercmp 12 =
// second argument is newer), then any revision change bumps it
let ec = sh("rpmdev-vercmp '" + old_tag + "' '" + new_tag + "'", #{}).ctx.rc;
let bump;
try {
	bump = find(`(?m)^%global[ \t]+bumpver[ \t]+(\d+)`, rpm.get(), 1).parse_int();
} catch {
	bump = 0;
}
if ec == 12 {
	// new upstream tag: reset the counter and move the version base
	rpm.global("bumpver", "0");
	rpm.set(sub(
		`(?m)^(Version:[ \t]*)[0-9.]+`,
		`Version:\t` + new_tag,
		rpm.get()));
	bump = 0;
} else if ec != 0 {
	terminate("hyprland-git: rpmdev-vercmp returned " + ec + " (upstream tag older than the spec?)");
}
if rpm.changed() || old_commit != new_commit || old_protocols != new_protocols ||
		old_udis86 != new_udis86 || old_date != new_date || new_tag != old_tag {
	rpm.global("bumpver", "" + (bump + 1));
}
