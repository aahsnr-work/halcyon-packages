# TODOs

-> All the tasks in the following unchecked boxes need to be done in the order they appear.

- [x] `Important`: This fedora copr must have the highest priority. Packages available in this copr repo should not be installed from fedora, terra or any other copr repo. All hyprland build dependencies and other packages that start with _hypr_ must be installed from this copper.
  - Done — `repo/halcyon.repo` consumer drop-in (Copr baseurl + project GPG key + `priority=1`). See notes/task-1-repo-priority.md.

- [x] [NOTE: Latest stable branch must be used] **hyprland**
  - Done — upstream keeps no `stable` branch; the sweeper now resolves the newest `vX.Y.Z-b` bugfix branch and pins its tip. See notes/task-2-hyprland-stable.md.

- [x] [NOTE: Latest stable branch must be used] **noctalia**
  - Done — no stable branch either; release-tracked (`github-release`), v5.1.0 packaged from Terra's noctalia-nightly recipe (C++/meson, no quickshell). See notes/task-3-noctalia.md.

- [x] `Important`: Create dnf spec files and other build-related files for the following packages:
  1. _zoxide_
  2. _fd-find_
  3. _cliphist_
  - Done — all three batch 0. zoxide/fd-find are rust source builds from the crates.io crate tarball; cliphist turned out to be **Go** (not Rust) and is a Go source build per the LionHeartP spec, nwg-look pattern. All validated locally (2026-09-26). See notes/task-4-new-packages.md.

- [x] `Important`: From all the rust source based packages, remove the reliance of andra-srpm-macros, so packages compiled with rust must rely on equivalent macros or methods in the dnf specs.
  - Done — all 12 rust specs carry the inline online-cargo prep + inline cargo-tree license pipeline; zero anda-srpm-macros BuildRequires left. Validated: Copr build 11035755 (rust-starship) green + local builds. See notes/task-5-rust-macros.md.

- [x] `Super-Important:` Perform a rigorous audit and review of the files/folders inside pkgs/ folder to make sure everything is in order and there are no errors and issues. Then apply the changes as needed. These include rust source based packages as well as the new packages: zoxide, fd-find, cliphist
  - Done — 51/51 specs parse clean in a Terra-macro buildroot; macro-in-comment landmines stripped (bun cava obsidian pyprland chafa zotero pixi), missing changelogs added, texlive generator template fixed. The local build pass later caught the Terra-only-macro class (%{_hicolordir}/%{_appsdir} in yazi + noctalia) and the cliphist language mistake — all fixed. See notes/task-6-pkgs-audit.md + notes/task-9-local-builds.md.

- [x] `Important`: Make the update happen weekly on Mondays only.
  - Done — update.yml cron `17 04 * * 1`. See notes/task-7-weekly-sweep.md.

- [x] Is dnf.conf in .github/workflows/builder still needed.
  - Answered: no — already deleted during the 2026-09-25 audit; nothing references it. See notes/task-8-dnfconf.md.

- [x] Then perform a local build of rust-based packages, hyprland, hyprland build dependencies, and other other hyprland related packages using a local podman instance, making sure you follow everything according to AGENTS.md file.
  - Done — 29/29 green in mock with the exact Copr buildroot (17 first pass + 12 retry): the whole hyprland closure including hyprland itself, all 12 rust source builds, the new packages, yazi and noctalia. Failures found on the way (harness SRPM-name glob, yazi/noctalia Terra-only %files macros, cliphist-is-Go, missing LICENSE.dependencies claims) were fixed and rebuilt green. See notes/task-9-local-builds.md.

- [ ] `Important` — **deferred**: the push below was postponed by the maintainer; a rolling-texlive redesign (notes/texlive-rolling-plan.md) is planned first. The cascade will ride the eventual push.

```bash
gh secret set COPR_CLICONF --repo aahsnr-work/halcyon-packages < ~/.config/copr   # already set (2026-09-25)
git add -A && git commit -m "migrate builds to Fedora Copr; replace the anda sweep with ci/sweep" && git push
# no separate `gh workflow run copr-build.yml` — the push itself triggers the
# cascade (path filter); a dispatched duplicate just queues behind it
```

## Local build validation ledger (mock, exact Copr buildroot)

- [x] hyprutils — OK
- [x] hyprlang — OK
- [x] hyprwayland-scanner — OK
- [x] hyprland-protocols — OK
- [x] glaze — OK
- [x] hyprland-qt-support — OK
- [x] aquamarine — OK
- [x] hyprcursor — OK
- [x] hyprgraphics — OK
- [x] hyprwire — OK
- [x] xdg-desktop-portal-hyprland — OK
- [x] noctalia-greeter-git — OK
- [x] texlab — OK
- [x] hyprland — OK
- [x] hyprland-guiutils — OK
- [x] hyprpwcenter — OK
- [x] hyprshutdown — OK
- [x] atuin — OK
- [x] bat — OK
- [x] dust — OK
- [x] eza — OK
- [x] starship — OK (also Copr build 11035755 green)
- [x] tealdeer — OK
- [x] zellij — OK
- [x] yazi — OK (after Terra-macro %files fix)
- [x] noctalia — OK
- [x] zoxide — OK
- [x] fd-find — OK
- [x] cliphist — OK (rewritten as a Go source build)
- [x] bitwarden — OK
- [x] bun — OK
- [x] lazygit — OK
- [x] marksman — OK
- [x] opencode — OK
- [x] pandoc — OK
- [x] pixi — OK
- [ ] kitty — failed mock (2026-09-26); diagnosis pending, rebuild queued
- [ ] cava — pending
- [ ] chafa — pending
- [ ] distroshelf — pending
- [ ] gnuplot — pending
- [ ] nwg-look — pending
- [ ] pyprland — pending
- [ ] qt6ct — pending
- [ ] xwiimote-ng — pending
- [ ] ticktick — pending
- [ ] uv — pending
- [ ] zotero — pending
- [ ] obsidian — pending
- [ ] hyprtoolkit — pending
- [ ] onlyoffice-desktopeditors — pending (heavy: 363 MB vendor RPM)
- [ ] texlive-\* groups (40) — excluded from this ledger; they roll via the
      biweekly texlive workflow (see notes/texlive-rolling-plan.md); five
      representative local builds are planned there (basic, latex, langcjk,
      meta, fontsextra)

The pending set was mid-run when the maintainer cancelled all builds
(2026-09-26); relaunch in two parallel containers is pending instruction.
