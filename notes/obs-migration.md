# OBS attempt — RETIRED (2026-09-25)

The OBS migration was applied end-to-end and then abandoned the same day by
decision: **the build system is and stays GitHub Actions + anda (mock) +
Pages/R2.** The `home:halcyon041` project on build.opensuse.org and its
artifacts (scmsync metas, the `runservice` token, the GitHub webhook) are
leftovers to delete, not to maintain.

What the attempt cost/was learned (kept here so nobody re-learns it):

- scmsync packages on OBS get NO automatic download of remote `Source:` URLs
  (classic packages do). The sanctioned fix is `#!RemoteAsset` comments
  before remote Source lines (pbuild/obs-build asset download, server-side,
  offline VM). The marks in the specs are inert rpm comments — left in
  place, harmless for anda/mock.
- OBS build VMs have no network (obs-docu, Security Concepts) — anything
  fetching at %build time (rust `cargo_prep_online`, nwg-look's Go proxy,
  distroshelf's meson-cargo) can never build there without vendoring.
- scmsync does not watch GitHub: pushes need notification. `/trigger/webhook`
  on the frontend is the SCM/CI `workflow`-token integration; for plain
  `runservice` tokens the endpoint is
  `POST https://api.opensuse.org/trigger/runservice?project=…&package=…`
  with `Authorization: Token <string>` (verified working, HTTP 200).
- Download-on-demand (`<download>`) in project meta is admin-gated on the
  public instance (HTTP 403), so the lionheartp/Hyprland Copr could not be
  attached; the externals (glaze, hyprwire, hyprtoolkit) were ported
  in-repo instead — that part stays useful regardless of OBS.
- OBS rebuild mode default is `transitive` on the repository element in
  project meta; unbuilt sibling deps make `osc build` fail server-side with
  `unresolvable` (no local resolution, no extra-repo injection).

Side effects that remain (all useful, none OBS-dependent): the renamed
packages (hyprland, noctalia), the self-hosted Copr externals, the batch
renumber (hyprtoolkit dependents at 3, texlive at 4), the
`%define debug_package %{nil}` sweep, and the workflow-file fixes that made
Actions actually run (env-context in container.image, the heredoc/pipe
stdin bug, buildx cache export).

OBS-side cleanup commands (user, optional):
```bash
osc rdelete home:halcyon041          # deletes project + all packages
osc token --delete 12525             # the runservice token
gh api -X DELETE repos/aahsnr-work/halcyon-packages/hooks/685448936
```
