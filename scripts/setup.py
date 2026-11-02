#!/usr/bin/env python3
"""Restore the frozen dedicated switch; never select or alter another switch."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
config = json.loads(Path("environment.json").read_text())
switch = os.environ.get("FORESTER_SWITCH", config["switch"])
for program in ("opam", "git"):
    if not shutil.which(program):
        sys.exit(f"Install {program} first; see README.md.")
try:
    import lxml.etree
except ImportError:
    sys.exit("Install Python lxml first; see README.md. No system packages were changed.")
switches = subprocess.check_output(["opam", "switch", "list", "--short"], text=True).splitlines()
if switch not in switches:
    subprocess.run(["opam", "switch", "create", switch, "--empty", "--no-switch", "--repos=default", "-y"], check=True)
    subprocess.run(["opam", "switch", "import", "--switch=" + switch,
                    "opam-switch.export", "-y", "--jobs=4"], check=True)
else:
    for command, expected in ((["ocamlc", "-version"], config["ocaml"]),
                               (["forester", "--version"], config["forester"])):
        result = subprocess.run(["opam", "exec", "--switch=" + switch, "--"] + command,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode or result.stdout.strip() != expected:
            detail = (result.stderr.strip() or result.stdout.strip() or
                      f"command exited with status {result.returncode}") if result.returncode else result.stdout.strip()
            restore = shlex.join(["opam", "switch", "import", "--switch=" + switch,
                                  "opam-switch.export", "--jobs=4"])
            retry = shlex.join(["make", "setup", "FORESTER_SWITCH=" + switch])
            sys.exit(f"Switch {switch!r} does not provide {command[0]} {expected}.\n"
                     f"Found: {detail}\n"
                     "The switch was not modified. If this is your dedicated forest switch, "
                     "finish or restore its packages from the pinned export:\n"
                     f"  {restore}\n  {retry}\n"
                     "Otherwise select an existing compatible switch or a new FORESTER_SWITCH name; "
                     "see README.md under Restoration.")
if not (ROOT / "theme/default.xsl").exists():
    subprocess.run(["git", "submodule", "update", "--init", "--", "theme"], check=True)
revision = subprocess.check_output(["git", "-C", "theme", "rev-parse", "HEAD"], text=True).strip()
if revision != config["theme_revision"]:
    sys.exit("Theme differs from the recorded revision; see README.md. Existing theme was not overwritten.")
print(f"Ready: Forester {config['forester']}, OCaml {config['ocaml']}, switch {switch}.")
print("Use make build, make check, or make serve. Your default opam switch is unchanged.")
