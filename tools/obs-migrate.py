#!/usr/bin/env python3
"""Migrate halcyon-packages to OBS via per-package scmsync.

Generates and (with --apply) applies the OBS metadata:

  project: home:<user>:halcyon — Fedora 44 target (x86_64) with the
           lionheartp/Hyprland Copr attached as a download-on-demand repo
  package: one per ci/packages.toml entry, scmsync pointing at this repo's
           `anda/<pkg>` subdirectory, tracking main

texlive-texmf is excluded — it stays on the R2 flow (multi-GB, see
notes/obs-migration.md).

Usage:
  OBS_USER=<login> tools/obs-migrate.py            # dry run: print XML + osc commands
  OBS_USER=<login> tools/obs-migrate.py --apply    # run the osc commands

Prereqs: `osc` installed and logged in (osc login / ~/.config/osc/oscrc);
GitHub repo pushed (scmsync fetches from it).
"""
import argparse, os, sys, xml.etree.ElementTree as ET

try:
    import tomllib
except ModuleNotFoundError:
    sys.exit("python 3.11+ (tomllib) required")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITHUB_URL = "https://github.com/aahsnr-work/halcyon-packages"
BRANCH = "main"
EXCLUDE = {"texlive-texmf"}  # stays on the R2 flow
COPR_URL = ("https://download.copr.fedorainfracloud.org/results/"
            "lionheartp/Hyprland/fedora-44-x86_64/")


def packages():
    data = tomllib.load(open(f"{REPO}/ci/packages.toml", "rb"))
    return [name for name in data if name not in EXCLUDE]


def project_meta(project):
    prj = ET.Element("project", name=project)
    ET.SubElement(prj, "title").text = "halcyon-packages"
    ET.SubElement(prj, "description").text = (
        "halcyon image packages: hand-maintained RPMs built from "
        "github.com/aahsnr-work/halcyon-packages via scmsync. "
        "texlive-texmf publishes separately to Cloudflare R2.")
    build = ET.SubElement(prj, "build")
    ET.SubElement(build, "enable")
    pub = ET.SubElement(prj, "publish")
    ET.SubElement(pub, "enable")
    repo = ET.SubElement(prj, "repository", name="Fedora_44")
    ET.SubElement(repo, "path", project="Fedora:44", repository="standard")
    # hyprwm stack needs what Fedora lacks (glaze-static, hyprtoolkit,
    # hyprwire, ...) — the same Copr the mock buildroot carries
    ET.SubElement(repo, "download", arch="x86_64", repotype="rpmmd",
                  url=COPR_URL)
    ET.SubElement(repo, "arch").text = "x86_64"
    return ET.tostring(prj, encoding="unicode")


def package_meta(project, pkg):
    p = ET.Element("package", name=pkg, project=project)
    ET.SubElement(p, "title").text = pkg
    ET.SubElement(p, "description").text = (
        f"halcyon-packages: {pkg} (source: anda/{pkg}, tracking main)")
    scmsync = ET.SubElement(p, "scmsync")
    scmsync.text = f"{GITHUB_URL}?subdir=anda/{pkg}#{BRANCH}"
    return ET.tostring(p, encoding="unicode")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("OBS_USER"),
                    help="OBS login (or set OBS_USER)")
    ap.add_argument("--project", help="default: home:<user>:halcyon")
    ap.add_argument("--apply", action="store_true",
                    help="actually run the osc commands")
    args = ap.parse_args()
    if not args.user:
        sys.exit("set OBS_USER or pass --user")
    project = args.project or f"home:{args.user}:halcyon"

    pkgs = packages()
    print(f"# {len(pkgs)} packages -> {project} (excluded: {sorted(EXCLUDE)})\n")

    prj_xml = project_meta(project)
    print(f"# --- project meta ({project}) ---\n{prj_xml}\n")
    print(f"osc meta prj {project} -F /tmp/obs-prj.xml")

    for pkg in pkgs:
        xml = package_meta(project, pkg)
        print(f"# --- {pkg} ---\n{xml}")
        print(f"osc meta pkg {project} {pkg} -F /tmp/obs-pkg-{pkg}.xml\n")

    if args.apply:
        open("/tmp/obs-prj.xml", "w").write(prj_xml)
        os.system(f"osc meta prj {project} -F /tmp/obs-prj.xml")
        for pkg in pkgs:
            f = f"/tmp/obs-pkg-{pkg}.xml"
            open(f, "w").write(package_meta(project, pkg))
            rc = os.system(f"osc meta pkg {project} {pkg} -F {f}")
            if rc != 0:
                sys.exit(f"failed: {pkg}")
        print(f"\nDone. Monitor: osc results -l {project}  "
              f"Repos: https://download.opensuse.org/repositories/{project.replace(':', ':')}/")
    else:
        print("# dry run — pass --apply to execute")


if __name__ == "__main__":
    main()
