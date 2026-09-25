// Version sweeps the latest GitHub release tag (a date like 2026-02-08);
// the raw tag goes into %%markstag for the source URLs and the version is
// the tag with dashes converted to dots (RPM versions cannot carry dashes).
let tag = gh("artempyanykh/marksman");
rpm.global("markstag", tag);
rpm.version(sub("-", ".", sub("-", ".", tag)));
