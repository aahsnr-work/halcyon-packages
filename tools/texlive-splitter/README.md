# TeX Live grouped-RPM splitter

Converts a dated tlnet-archive snapshot into ONE `texlive-texmf` source
package whose subpackages mirror Arch's grouping (texlive-basic,
texlive-binextra, texlive-latexextra, texlive-fontsextra, texlive-lang*,
texlive-doc, ...).

Wired into CI via `adapt-spec.py` (see the repo TODO.md): the generated
spec's `%files` lists reference the local install staging tree, so adapt-spec.py
rewrites the spec to stage the snapshot from the dated archive at %build time
before it can build as an SRPM.

Usage:

    ./splitter.py --snapshot 20260901 \
        [--archive-root https://texlive.info/tlnet-archive] [--out ./generated]

Steps performed:

1. install-tl --profile into a staging dir from the dated snapshot
   (scheme-medium, docfiles installed; docs land in the texlive-doc subpackage)
2. parse tlpkg/texlive.tlpdb -> collection blocks (runfiles, deps,
   AddFormat/addMap/AddHyphen fragments)
3. generate one spec, `./generated/texlive-texmf.spec`, with a
   `%package -n texlive-<group>` subpackage per Arch-named group

Not implemented (prints hints only):

4. repackaging the staging tree into buildable sources + a mock/Copr build of
   the whole set atomically (one snapshot for ALL groups)
5. publishing into the Copr project + bumping consumers

The Arch reference implementation: gitlab.archlinux.org/archlinux/packaging/
packages/texlive-texmf (prepare() parsing + pacman hook fragments).
