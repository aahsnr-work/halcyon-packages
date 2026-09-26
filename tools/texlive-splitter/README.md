# TeX Live rolling per-group packager

Turns a tlnet-archive snapshot into **40 separate specs** — one per
Arch-named collection group (`texlive-basic`, `texlive-latex`,
`texlive-fontsextra`, ..., the `texlive-lang*` set) plus `texlive-meta`
(the scheme-full catch-all) — living at `pkgs/texlive-<group>/`. Batch 5,
owned by the biweekly roll (`.github/workflows/texlive-update.yml`).

Tools:

- **splitter.py** — the parsing/partition library: `parse_tlpdb()` +
  `partition(packages, scheme, docs=False)`. The partition claims every
  texmf-dist file for exactly one group (topologically ordered
  collections first, level-1 members before transitive reachers) and
  tracks each group's member tarballs.
- **emit_groups.py** — renders one spec per group + meta: `%build` wgets
  the group's member tarballs from the dated snapshot
  (`<snapshot>/tlnet/archive/<pkg>.tar.xz`), merges the relocatable
  top-level dirs into one `texmf-dist` tree, prunes `doc/` (no
  documentation ships) and generates the mktexlsr-format `ls-R` in
  texlive-basic. Output is a pure function of the snapshot date.
- **roll.py** — the driver: probe the newest daily snapshot (xz-magic
  check; texlive.info fronts the archive with Anubis, which wants a
  wget/curl-shaped User-Agent), fetch + decompress the tlpdb, render all
  specs, write only byte-changed files, append missing registry entries.
  Idempotent: a second run against the same snapshot writes nothing.

Manual roll: `python3 tools/texlive-splitter/roll.py [--snapshot YYYYMMDD]`.

The Arch reference: gitlab.archlinux.org/archlinux/packaging/packages/
texlive-* (the group list and the collection→group mapping mirror it).
