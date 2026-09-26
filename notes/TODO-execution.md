# notes/TODO-execution — 2026-09-26

Per-task record of the TODO.md execution (tasks done in file order). See the
per-task notes below; this file is the index and carries the decisions.

| # | task | state | notes file |
|---|------|-------|------------|
| 1 | Copr repo = highest install priority | done | task-1-repo-priority.md |
| 2 | hyprland tracks the latest stable line | done | task-2-hyprland-stable.md |
| 3 | noctalia packaged (release-tracked) | done | task-3-noctalia.md |
| 4 | zoxide / fd-find / cliphist specs | done | task-4-new-packages.md |
| 5 | rust specs drop anda-srpm-macros | done | task-5-rust-macros.md |
| 6 | rigorous pkgs/ audit | done | task-6-pkgs-audit.md |
| 7 | sweep weekly on Mondays | done | task-7-weekly-sweep.md |
| 8 | dnf.conf still needed? | answered: no — deleted | task-8-dnfconf.md |
| 9 | local podman builds of rust + hyprland sets | done — 29/29 green | task-9-local-builds.md |
| 10 | secret + commit + push + cascade | **deferred by maintainer** (see below) | task-10-cutover.md |

Decisions taken without a task box:

- copr-setup notes stay folded into README.md (notes/ was intentionally
  deleted earlier); this folder exists for the TODO-task records only.
- texlive-texmf and onlyoffice smoke builds were left alone per instruction;
  the fixes already applied to their specs ride the cascade.
- Task 10 (the push) was deferred by the maintainer after task 9 went
  green — before it runs, a rolling-texlive redesign is planned instead
  (notes/texlive-rolling-plan.md).
- hyprland "stable" = the newest `vX.Y.Z-b` bugfix branch (upstream keeps no
  `stable` branch); noctalia "stable" = the latest release tag (same reason).
