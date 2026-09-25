// Version sweeps the GitLab releases of opencode.net/trialuser/qt6ct (the
// canonical repo; the GitHub mirror lags behind). The spec pins the release
// commit: the Source0 archive URL follows the %global commit.
// (GitLab note: the API needs the www. host and the bare project id.)
let release = get_json("https://www.opencode.net/api/v4/projects/5459/releases?per_page=1")[0];
rpm.version(release.tag_name);
rpm.global("commit", release.commit.id);
