// Version sweeps oven-sh/bun's LATEST file on the main branch (bun publishes
// no GitHub release feed; the LATEST file is the official channel). Version
// tracks the -baseline build of the release zip.
rpm.version(get("https://raw.githubusercontent.com/oven-sh/bun/main/LATEST"));
