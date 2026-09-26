# Task 4 — zoxide, fd-find, cliphist

New rust packages, batch 0, all sweep `github-release`:

| package   | upstream              | version | crates.io | source              |
|-----------|-----------------------|---------|-----------|---------------------|
| zoxide    | ajeetdsouza/zoxide    | 0.10.0  | yes       | static.crates.io    |
| fd-find   | sharkdp/fd            | 10.5.0  | yes       | static.crates.io    |
| cliphist  | sentriz/cliphist      | 0.7.0   | n/a       | GitHub tag tarball  |

- Written against the new inline online-cargo prep (task 5) — born without
  anda-srpm-macros; bin-crate layout (no devel/feature subpackages), license
  macros generate LICENSE.dependencies at build.
- **cliphist correction (task 9)**: the first draft assumed Rust from the
  crates.io 404, but upstream is **Go**. Rewritten as a Go source build
  per the maintainer's pointer to LionHeartP/hyprlandRPM's cliphist spec —
  nwg-look pattern (module proxy at %build, no go2rpm machinery, no vendor
  tarball); version embedded by upstream's go:embed version.txt.
- Fedora conflicts: zoxide 0.9.8, fd-find 10.4.2, cliphist 0.7.0 (equal) —
  all lose to priority=1 (task 1). Crate tarball URLs verified (200)
  before writing.
