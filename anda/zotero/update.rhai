// Version sweeps the latest git tag of zotero/zotero (tags are cut without
// GitHub releases; rpm.version strips the leading v itself).
rpm.version(gh_tag("zotero/zotero"));
