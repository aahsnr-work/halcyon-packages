# DEFERRED: opencode

Not in `copr/packages.toml`, so Copr never builds it. Everything is in place
(script.sh, fetch.sh, a fixed spec) — it just has not had a successful build
yet:

- Source0/URL pointed at sst/opencode, renamed to anomalyco/opencode.
- The release asset name was wrong: the real one is opencode-linux-x64.zip.
- %prep used to curl the zip; Copr build chroots have no network by default,
  so it now unzips the file the source method script provides.

To enable: run `copr/test-source.sh opencode`, then `copr/submit.py --only
opencode`, and add the `[opencode]` table to `copr/packages.toml` once the
build is green.
