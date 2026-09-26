# Task 6 — rigorous pkgs/ audit (51 packages)

Method: scripted checks over every registry entry + a container-wide
`rpmspec -P` parse (the definitive detector for macro-in-comment landmines,
since the image carries the Terra macro set that Copr's buildroot also sees)
+ spectool-URL reachability for every Source.

## Found and fixed

- **bun** — `%define debug_package %nil` normalized to `%{nil}`; the written
  changelog the rule requires was retro-added (spec predates the rule).
- **cava, obsidian, pyprland** — no `%changelog` at all; retro-added.
- **chafa** — `pkg_libs_files` / `pkg_devel_files` / `pkg_static_files`
  named with `%` inside comments; the macros are defined in the buildroot,
  so they EXPANDED into the comments and broke parsing. % sigils stripped.
- **zotero** — same class: `%git_clone`, `%terra_appstream`,
  `%desktop_file_install` in comments expanded mid-parse. Stripped.
- **pixi** — `%cargo_prep_online` in a comment expanded to the macro's
  multiline body → "Unknown tag: (". Reworded.
- **bun (second landmine)** — `%pkg_completion -bfz bun` in a comment
  expanded into fake `%description -n bun-bash-completion` stanzas. Stripped.
- **zoxide/fd-find/cliphist (my new specs)** — `%description %{summary}.`
  on one line parses the expansion as a language-name argument
  ("Too many names"); summary moved to its own line (main + subpackage).
- **texlive-texmf (generated)** — lacked the mandatory debug_package define
  and a changelog; both added to `adapt-spec.py`'s HEADER_TEMPLATE and the
  spec regenerated from it (never hand-edit the generated file).

## Final state

- `rpmspec -P`: **51/51 specs parse clean** (in the builder container, with
  the Terra macro set present, mirroring Copr's buildroot).
- debug_package nil + written changelog: 51/51 (texlive's come from the
  generator template).
- Local Source/Patch references: all present in their package dirs.
- Source URLs: all reachable (spectool list + HEAD checks).
- Mandatory defines spot-checked against AGENTS.md conventions.
