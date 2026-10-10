#!/usr/bin/env python3
"""Compile native Forester trees, then apply the pinned XSLT locally."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from lxml import etree

import check

ROOT = Path(__file__).resolve().parents[1]


def run():
    os.chdir(ROOT)
    check.sources()
    env = json.loads(Path("environment.json").read_text())
    switch = os.environ.get("FORESTER_SWITCH", env["switch"])
    prefix = ["opam", "exec", "--switch=" + switch, "--"]
    for command, version in ((["ocamlc", "-version"], env["ocaml"]),
                             (["forester", "--version"], env["forester"])):
        actual = subprocess.check_output(prefix + command, text=True).strip()
        check.require(actual == version, f"Expected {command[0]} {version}, found {actual}")
    revision = subprocess.check_output(["git", "-C", "theme", "rev-parse", "HEAD"], text=True).strip()
    check.require(revision == env["theme_revision"], "Theme revision differs from environment.json")
    check.require(not subprocess.check_output(["git", "-C", "theme", "status", "--porcelain"], text=True).strip(),
                  "Theme has local edits; put customizations in assets/ instead")
    out = Path("output")
    check.require(not out.is_symlink(), "Refusing to overwrite a symlinked output directory")
    if out.exists():
        shutil.rmtree(out)
    result = subprocess.run(prefix + ["forester", "build"], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    Path("build.log").write_text(result.stdout)
    print(result.stdout, end="")
    check.require(result.returncode == 0, f"Forester failed ({result.returncode}); see build.log")
    plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    check.require(not re.search(r"\b(error|warning)\b", plain, re.I),
                  "Forester reported diagnostics; see build.log")
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    transform = etree.XSLT(etree.parse("assets/project.xsl", parser),
                          access_control=etree.XSLTAccessControl(read_network=False, write_network=False))
    for source in sorted(out.rglob("index.xml")):
        document = etree.parse(str(source), parser)
        # Use actual HTML documents for every page link, including transcluded routes.
        for node in document.iter():
            for attr in ("href", "src"):
                if node.get(attr):
                    node.set(attr, node.get(attr).replace("/index.xml", "/index.html"))
            if node.tag == "{http://www.forester-notes.org}route" and node.text:
                node.text = node.text.replace("/index.xml", "/index.html")
        rendered = transform(document)
        for node in rendered.iter():
            if isinstance(node.tag, str) and node.tag.startswith("{http://www.w3.org/1999/xhtml}"):
                node.tag = etree.QName(node).localname
        etree.cleanup_namespaces(rendered)
        rendered.getroot().set("lang", "en")
        head = rendered.find("head")
        head.insert(0, etree.Element("meta", charset="utf-8"))
        head.append(etree.Element("link", rel="stylesheet", href="/project.css"))
        source.with_suffix(".html").write_bytes(etree.tostring(
            rendered, method="html", encoding="utf-8", doctype="<!DOCTYPE html>"))
    manifest = out / "forest.json"
    manifest.write_text(manifest.read_text().replace("/index.xml", "/index.html"))
    (out / "index.html").write_text('<!DOCTYPE html><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=/index/index.html">'
        '<title>Crossing-number forest</title><a href="/index/index.html">Open the forest</a>\n')
    for directory in ("source-material", "computations"):
        shutil.copytree(directory, out / directory, ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("source-map.json", "lean-map.json", "LICENSE", "NOTICE"):
        shutil.copy2(name, out / name)
    shutil.copy2("assets/project.css", out / "project.css")
    check.output(check.sources())
    print("Built output/ — entry page: /index/index.html")


if __name__ == "__main__":
    try:
        run()
    except (ValueError, OSError, subprocess.CalledProcessError, etree.Error) as exc:
        sys.exit(str(exc))
