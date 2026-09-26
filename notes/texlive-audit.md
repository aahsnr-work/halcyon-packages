# notes/texlive-audit — implementation review before first build (2026-09-26)

Audit of the rolling per-group texlive implementation (emit_groups.py,
roll.py, the 40 generated specs, texlive-update.yml, copr-build.yml wave 6,
matrix.py cascade) against the real tlnet-archive wire behavior and Fedora
Copr build/consume semantics. Grounded against live checks: member tarball
inspection (latex, kpathsea) and Fedora file-ownership queries
(repoquery in the fedora-44 toolbox).

## P0 — must fix before any build

1. **Tarball extraction is wrong for relocatable packages.**
   `archive/latex.tar.xz` unpacks `tex/…`, `makeindex/…` — paths relative
   to the **texmf root** (tlpdb writes these as `RELOC/…`; the wire tarballs
   use the real subpaths). `archive/kpathsea.tar.xz` unpacks
   `texmf-dist/…` + `tlpkg/…` (non-relocatable). The emitted `%build`
   copies only `raw/RELOC/.` and `raw/texmf-dist/.` into the staging tree —
   neither exists for relocatable packages, so every group built mainly
   from relocatable members (latex, fontsextra, …) would stage an **empty
   tree** and fail %files loudly. Fix in emit_groups.py SPEC_BODY: after
   `tar -xJf`, merge **every top-level dir of raw except `tlpkg` and `bin`**
   into `staging/texmf-dist/` (covers tex/, fonts/, dvips/, makeindex/, …,
   RELOC/ and texmf-dist/ alike), then run the existing doc/source prune
   last. Non-relocatable `tlpkg/` (the per-tarball tlpdb) must never land
   in the tree.

2. **Co-installability with Fedora's texlive is undecided — the consume
   story breaks today.** Fedora's texlive-latex owns
   `/usr/share/texlive/texmf-dist/tex/latex/base/latex.ltx` — exactly what
   our texlive-latex claims; our texlive-basic claims
   `web2c/updmap.cfg`, `web2c/texmf.cnf`, … which Fedora's
   texlive-kpathsea/base/filesystem own. Two conflict classes:
   - **Same-named packages** (texlive-latex, texlive-fontsextra, …):
     fine — higher Version (20260925 vs Fedora's year-based) + priority=1
     makes them a normal upgrade; rpm handles divergent file lists within
     one NEVRA name.
   - **Cross-named owners** (our texlive-basic vs texlive-kpathsea /
     texlive-base / texlive-filesystem; our texlive-fontsextra vs
     texlive-amsfonts, texlive-mflogo, …): **hard rpm file conflicts** —
     repo priority does not resolve those; the dnf transaction aborts.
   Decision needed (maintainer): either (a) add `Conflicts:` (+ Obsoletes
   where same-name-shadowing applies) from our groups to the overlapping
   Fedora texlive data packages so `dnf install texlive-meta` can
   `--allowerasing` them cleanly, or (b) the halcyon image drops Fedora's
   texlive data packages entirely — which is impossible while keeping
   Fedora's engines (texlive-base ships binaries AND data), so realistically
   (a) plus an image-side transaction test, or (c) long-term: the
   texlive-bin split (ship engines ourselves, drop Fedora texlive wholly).
   Until decided, `dnf install texlive-*` on any Fedora-texlive system is
   NOT expected to work. The build side is unaffected (builds don't see
   the host system).

## P1 — fix before the first roll ships

3. **`ls-R` is written in the wrong format.** texlive-basic generates a
   flat sorted file list; kpathsea's ls-R database is directory-blocked
   (`% ./dir:` headers + indented entries). A flat list can confuse
   kpathsea lookups (entries are resolved relative to the preceding
   directory header). Either emit proper mktexlsr-format output (trivial
   awk grouping: for each directory, `% ./<dir>:` then its entries) or
   drop the ls-R claim entirely (kpathsea falls back to directory scans —
   slower, but correct). Prefers proper format for parity with install-tl.

## P2 — worth fixing, non-blocking

4. **Stale collections**: if upstream removes/renames a collection, its
   texlive-<group> dir + registry entry linger and the next roll leaves it
   pinned to an old snapshot (whose tarballs may 404 → loud build failure).
   Acceptable (rare; last grouping change 2023) but roll.py could WARN on
   registry texlive-* entries not produced by this roll.
5. **pyc noise**: texmf-dist/scripts contains .py files; Copr's brp
   python-bytecompile may drop .pyc next to them. `_unpackaged_files_
   terminate_build 0` tolerates it; just expect the noise in build logs.
6. **No `%check`** in the group specs (the monolith verified ls-R
   presence). Optional: a one-line `[ -f staging/texmf-dist/ls-R ]` (basic)
   / staged-file count sanity for the others.
7. **spectool `|| true` in submit5** is defensive but masks real spec
   breakage — fine as long as rpmbuild -bs itself is not masked (it
   isn't).

## Verified good (no action)

- Partition semantics byte-match the monolith's validated coverage
  (per-group counts within snapshot drift; deterministic first-claim
  ownership).
- `%files` paths are correct (`%{_tl_texmf}/…` = /usr/share/texlive/
  texmf-dist/…); ls-R, web2c configs, fonts all claimed as expected.
- texlive-meta: 39 `Requires: texlive-<group> = %{version}` lines, trivial
  %build, correct %doc.
- Versioned inter-group Requires keep all installed groups on one
  snapshot; every roll bumps all 40 Versions together so the pins stay
  satisfiable.
- Workflow chain submit4→wait4→submit5→wait5 correct (duplicate-key YAML
  checked); manifest emits batch5; matrix closure selects exactly the
  changed texlive dirs on a roll push.
- Roll driver: xz-magic probe (HTML placeholder defense), Anubis wget-UA,
  idempotence, registry auto-append, changelog dates derived from the
  snapshot date (no bogus weekdays).
- No-docs requirement enforced structurally (docfiles never claimed; doc/
  and source/ pruned post-extract — prune must run AFTER the P0-1 merge
  fix).

## Bottom line

Two P0 corrections (tarball merge rule; the Fedora co-installability
decision) and one P1 (ls-R format) stand between the current state and the
first local build. The local build of texlive-basic, texlive-latex,
texlive-meta and texlive-fontsextra is the gate that proves P0-1's fix and
the tarball model end-to-end.

## Addendum — what the first local builds found (2026-09-26, applied)

The audit fixes were applied (P0-1 merge rule, P1 ls-R, stale-entry
warning) plus three defects the builds then surfaced:

1. **The merge rule itself was wrong in a second way** (found via
   texlive-latex: 3,940 File-not-found, exactly the relocatable top
   dirs): the first fix FLATTENED relocatable tarballs
   (`cp -a raw/tex/.` → staging root), but the wire paths ARE the
   texmf-dist subpaths — `tex/` must land at `texmf-dist/tex/`, not
   `texmf-dist/`. Final rule: relocatable shapes (`tex`, `fonts`,
   `bibtex`, …) copy with the dir name preserved
   (`cp -a "$entry" staging/texmf-dist/`); only the `texmf-dist`/`RELOC`
   shapes merge contents.
2. **ls-R printf**: rpm collapses `%%` → `%` inside the run script, so the
   spec needs `%%%%` for printf to emit one literal `%` (basic failed:
   "printf: `R': invalid format character").
3. **Claim order** (found while verifying ownership before the build): the
   scheme-list order put kpathsea/latex into xetex/langjapanese. The
   partition now topologically sorts the collection DAG (deps first,
   alphabetical tie-break) and claims LEVEL-1 members across all
   collections before any transitive closure — kpathsea/texlive.infra →
   texlive-basic, latex → texlive-latex, jsclasses → texlive-langjapanese.

Re-rolled and verified: idempotent, 40/40 rpmspec-parse clean. First four
group builds with the final form: **basic, bibtexextra, binextra, context
all OK**; the full 40-group run was stopped by the maintainer and the
remaining 36 await a go.
