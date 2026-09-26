# Task 5 — rust packages drop anda-srpm-macros

Requirement: rust source builds must not rely on anda-srpm-macros.

## What terra's macros actually did (inspected in the builder container)

- `macros.cargo_extra`: `cargo_prep_online_sccache` = write
  `.cargo/config.toml` ([profile.rpm] from the rustflags macros, [build] with
  rustc/rustdoc + sccache wrapper, [env] CFLAGS/CXXFLAGS/LDFLAGS,
  [install] root, [term] verbose — NO [net] offline, NO local-registry
  replacement) + redefine `%__cargo` to a CARGO_HOME/RUSTC_BOOTSTRAP=1/
  RUSTFLAGS env wrapper, so Fedora's cargo_build/install/test macros run
  online against that config.
- `macros.caching`: `%__sccache` = /usr/bin/sccache.
- `cargo_license_online` / `cargo_license_summary_online`: cargo tree
  license reports — Fedora's cargo-rpm-macros 28 ships the same facility as
  `%cargo_license` / `%cargo_license_summary` (cargo-to-rpm based).

## Replacement (inline in each spec — no shared macro package)

The 12 rust source specs (atuin bat dust eza starship tealdeer texlab yazi
zellij — plus the task-4 crates zoxide fd-find cliphist, born in this style)
now carry, in %prep:

1. `%global _cargo_home …` + `%global __sccache /usr/bin/sccache`
2. the config.toml heredoc (identical sections to terra's, sccache wrapper
   included; no offline, no registry replacement)
3. `%{expand:%global __cargo /usr/bin/env CARGO_HOME=… RUSTC_BOOTSTRAP=1
   RUSTFLAGS='%{build_rustflags}' /usr/bin/cargo}` (RUSTC_BOOTSTRAP is what
   lets `%cargo_build`'s `-Z avoid-dev-deps` work on stable rust)

plus the license reports. First attempt used Fedora's `%cargo_license*` —
those go through cargo-to-rpm, whose license commands hardcode `--offline`,
which fails in the online build (Copr build 11035734: cargo refused because
the lockfile "needs to be updated but --offline was passed"). Final form is
an inline `%{__cargo} tree` pipeline replicating terra's
`cargo_license_online` output verbatim:

```
%{__cargo} tree -Z avoid-dev-deps --workspace --edges no-build,no-dev,no-proc-macro \
    --no-dedupe --target all --prefix none --format "# {l}" | sort -u
%{__cargo} tree -Z avoid-dev-deps --workspace --edges no-build,no-dev,no-proc-macro \
    --no-dedupe --target all --prefix none --format "{l}: {p}" \
    | sed -e "s: (proc-macro)::" | sort -u > LICENSE.dependencies
```

(`%{__cargo}` is the env-wrapper defined in the %prep block, so the tree
walk runs with the same CARGO_HOME/RUSTFLAGS as the build. `%files` must
claim `LICENSE.dependencies` — the task-4 bin crates initially didn't and
that is a guaranteed unpackaged-file failure.)

- `BuildRequires: anda-srpm-macros` removed everywhere (grep-verified zero);
  `cargo-rpm-macros >= 24` and `sccache` stay. The three new rust specs
  (task 4) were born in this style.
- The Terra 44 chroot repo stays configured (harmless; still a potential
  input for anything else), but nothing in pkgs/ needs it anymore.
- Validation: full-starship rebuild submitted to Copr after the change —
  green (build 11035755; the inline prep block + cargo-tree pipeline both
  exercised, LICENSE.dependencies generated in the log).
