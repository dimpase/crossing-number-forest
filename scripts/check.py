#!/usr/bin/env python3
"""Check this forest's explicit editorial conventions and local reading paths."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from lxml import etree, html

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"proved", "conjecture", "computational-evidence", "incomplete",
            "source-needed", "superseded", "proof-account"}
NS = {"f": "http://www.forester-notes.org"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def acyclic(graph, label):
    done = set()

    def visit(node, path):
        require(node not in path, f"{label} cycle: {' -> '.join(path + [node])}")
        if node in done:
            return
        for target in graph[node]:
            require(target in graph, f"{node}: missing {label} target {target}")
            visit(target, path + [node])
        done.add(node)

    for node in graph:
        visit(node, [])


def sources():
    notes, dependencies, inclusions = {}, {}, {}
    definitions, defined_terms = set(), {}
    for path in sorted((ROOT / "trees").rglob("*.tree")):
        addr = path.stem
        require(addr not in notes, f"Duplicate address: {addr}")
        require(re.fullmatch(r"index|cn-\d{4}", addr), f"Unexpected address: {addr}")
        text = path.read_text()
        require(not re.search(r"\\(?:subtree\s*\[|addr\s*\{)", text),
                f"{addr}: use one canonical address per file; extend the checker before using inline addresses")
        for field in ("title", "taxon"):
            require(re.search(r"\\" + field + r"\{[^{}]+\}", text), f"{addr}: missing {field}")
        pairs = re.findall(r"\\meta\{([^{}]+)\}\{([^{}]*)\}", text)
        meta = dict(pairs)
        require(len(meta) == len(pairs), f"{addr}: duplicate metadata field")
        for field in ("dependencies", "provenance"):
            require(meta.get(field, "").strip(), f"{addr}: missing {field}")
        status = meta.get("status")
        if status:
            require(status in STATUSES, f"{addr}: unknown status {status}")
        taxon = re.search(r"\\taxon\{([^{}]+)\}", text)[1]
        if taxon == "Definition":
            definitions.add(addr)
            require(r"\tag{definition}" in text, f"{addr}: missing definition tag")
            require(meta.get("defines", "").strip(), f"{addr}: list the defined terms in defines metadata")
            require(r"\em{" in text, f"{addr}: emphasize the term being defined")
            for term in meta["defines"].split(";"):
                term = term.strip().casefold()
                require(term and term not in defined_terms, f"{addr}: duplicate or empty defined term {term!r}")
                defined_terms[term] = addr
        if taxon not in {"Definition", "Overview", "Questions", "Reference"}:
            require(status is not None, f"{addr}: mathematical result needs status")
        if status in {"proved", "conjecture", "computational-evidence", "proof-account"}:
            require(r"\strong{Statement.}" in text, f"{addr}: missing Statement")
        if status in {"proved", "proof-account"}:
            require(r"\strong{Proof.}" in text, f"{addr}: missing Proof")
        if status == "source-needed":
            require(r"\strong{Missing source.}" in text, f"{addr}: explain the missing source")
        dependencies[addr] = re.findall(r"\]\((cn-\d{4}|index)\)", meta["dependencies"])
        require(meta["dependencies"] == "None." or dependencies[addr],
                f"{addr}: dependencies must be explicit note links or 'None.'")
        inclusions[addr] = re.findall(r"\\transclude\{([^{}]+)\}", text)
        notes[addr] = (text, meta)
    require("index" in notes, "Missing index tree")
    for addr in definitions:
        require(f"]({addr})" in notes["index"][0], f"{addr}: missing from the manual definition index")
    for addr, (text, _) in notes.items():
        targets = re.findall(r"\]\((cn-\d{4}|index)\)", text)
        targets += re.findall(r"\\ref\{([^{}]+)\}", text)
        for target in targets:
            require(target in notes, f"{addr}: unresolved reference {target}")
        if notes[addr][1].get("status") in {"proved", "proof-account"}:
            body = re.sub(r"\\meta\{[^{}]+\}\{[^{}]*\}", "", text)
            for target in set(dependencies[addr]) & definitions:
                require(f"]({target})" in body or r"\ref{" + target + "}" in body,
                        f"{addr}: cite definition {target} in the statement/proof, not only in metadata")
    acyclic(dependencies, "proof dependency")
    acyclic(inclusions, "transclusion")
    manifest = json.loads((ROOT / "source-material/manifest.json").read_text())["sources"]
    source_versions = {source["id"]: source["version"] for source in manifest}
    require(len(source_versions) == len(manifest), "Duplicate source ID in manifest")
    for source in manifest:
        if source.get("path"):
            path = ROOT / source["path"]
            require(hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"],
                    f"Source changed without updating its manifest: {path}")
    mappings = json.loads((ROOT / "source-map.json").read_text())["mappings"]
    keys = set()
    for entry in mappings:
        key = (entry["source_id"], entry["source_version"], entry["label"])
        require(entry["source_id"] in source_versions, f"Unknown mapped source: {key}")
        require(entry["source_version"] == source_versions[entry["source_id"]],
                f"Mapped source version differs from manifest: {key}")
        require(key not in keys, f"Duplicate source mapping: {key}")
        keys.add(key)
        if entry["status"] == "unresolved":
            require(entry["destination"] is None, f"Unverified source mapping: {key}")
            require(entry["placeholder"] in notes, f"Missing placeholder: {key}")
        else:
            require(entry["destination"] in notes, f"Missing mapped note: {key}")
    return notes


def output(notes):
    out = ROOT / "output"
    base_path = etree.parse(str(out / "index/index.xml")).getroot().get("base-url")
    require(base_path and base_path.startswith("/") and base_path.endswith("/"),
            "Missing or invalid site base path")
    pages = {}
    for path in out.rglob("*.html"):
        doc = html.parse(str(path))
        pages[path.resolve()] = doc
        require(not doc.xpath('//*[contains(@class, "error")]'), f"Rendered error in {path}")
    for addr, (source_text, meta) in notes.items():
        path = out / addr / "index.html"
        require(path.resolve() in pages, f"Missing rendered note: {addr}")
        doc = pages[path.resolve()]
        require(doc.getroot().get("data-base-url") == base_path,
                f"{addr}: search uses the wrong site base path")
        body = " ".join(doc.xpath("//body//text()"))
        require("Provenance" in body and "Proof dependencies" in body,
                f"{addr}: provenance/dependencies are not visible")
        if meta.get("status"):
            require(meta["status"] in body, f"{addr}: status is not visible")
        xml = etree.parse(str(out / addr / "index.xml"))
        require(not xml.xpath("//f:error", namespaces=NS), f"{addr}: Forester emitted an error node")
        # Forester's native \tag command otherwise silently consumes TeX tags.
        # A verbatim escape must carry each numbered equation label into TeX.
        math = "\n".join(xml.xpath("/f:tree/f:mainmatter//f:tex/text()", namespaces=NS))
        for label in re.findall(r"\\tag\{(\d+\.\d+)\}", source_text):
            require(re.search(r"\\tag\s*\{\s*" + re.escape(label) + r"\s*\}", math),
                    f"{addr}: equation ({label}) lost its TeX label; use a verbatim escape")
        if xml.xpath("/f:tree/f:frontmatter/f:taxon[text()='Definition']", namespaces=NS):
            heading = doc.xpath("//article/section[@data-taxon='Definition']/details/summary/header/h1")
            require(heading and addr in " ".join(heading[0].itertext()),
                    f"{addr}: definition needs a visible tagged heading")
        for citation in doc.xpath("//a[@data-note-tag]"):
            tag = citation.get("data-note-tag")
            require(tag in notes and f"[{tag}]" in " ".join(citation.itertext()),
                    f"{addr}: citation omits its visible canonical tag {tag}")
    for path, doc in pages.items():
        for node in doc.xpath("//*[@href or @src]"):
            for attr in ("href", "src"):
                value = node.get(attr)
                if not value:
                    continue
                url = urlsplit(value)
                if url.scheme or url.netloc:
                    require(attr != "src" and node.tag != "link", f"Remote reading asset: {value}")
                    continue
                if url.path.startswith("/"):
                    require(url.path.startswith(base_path), f"Link escapes site base path: {value}")
                    target = (out / unquote(url.path[len(base_path):])).resolve()
                else:
                    target = (path.parent / unquote(url.path)).resolve()
                if not url.path:
                    target = path
                if target.is_dir():
                    target /= "index.html"
                require(target.is_relative_to(out.resolve()), f"Link escapes output: {value}")
                require(target.exists(), f"{path.relative_to(out)}: missing {value}")
                if url.fragment and target in pages:
                    require(pages[target].xpath("//*[@id=$id]", id=unquote(url.fragment)),
                            f"{path.relative_to(out)}: missing anchor {value}")
    search = json.loads((out / "forest.json").read_text())
    require({entry["uri"] for entry in search} == set(notes), "Search index omits or adds notes")
    for entry in search:
        route = entry["route"]
        require(route.startswith(base_path), f"Search route escapes site base path: {route}")
        target = out / route[len(base_path):]
        if target.is_dir():
            target /= "index.html"
        require(target.resolve() in pages, f"Search route has no rendered page: {route}")
    print(f"Checked {len(notes)} notes, rendered links/assets, metadata, and dependency/transclusion graphs.")
    for addr, (_, meta) in notes.items():
        if meta.get("status") in {"source-needed", "incomplete"}:
            print(f"OUTSTANDING {addr}: {meta['status']}")
    print("These are site checks; they do not certify mathematical proofs.")


if __name__ == "__main__":
    try:
        notes = sources()
        if "--sources" not in sys.argv:
            output(notes)
    except (ValueError, OSError, KeyError, etree.Error) as exc:
        sys.exit(str(exc))
