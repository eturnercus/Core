#!/usr/bin/env python3
"""Turn every "new file" section of a patch into a modification diff.

Paperweight imports any mc-dev source a patch mentions into src/main/java *before* running
git am, so a patch that declares the same path with `new file mode` / `--- /dev/null` fails with
CONFLICT (add/add). Any vanilla file we start patching has to be diffed against its vanilla
content instead, with real blob hashes on the index line so `git am --3way` can rebuild the base.

Usage: fix_newfiles.py <patch-file> [more-patch-files...]
"""
import io
import os
import subprocess
import sys

REPO = "/root/eturlia-src"
MCDEV = os.path.join(REPO, ".gradle/caches/paperweight/upstreams/paper/Paper-Server/"
                           ".gradle/caches/paperweight/mc-dev-sources")
SRC = os.path.join(REPO, "Folia-Server/src/main/java")
PREFIX = "src/main/java/"


def hash_object(path):
    return subprocess.check_output(["git", "hash-object", path], text=True).strip()


def modify_section(path_in_patch):
    rel = path_in_patch[len(PREFIX):]
    vanilla = os.path.join(MCDEV, rel)
    modified = os.path.join(SRC, rel)
    if not os.path.exists(vanilla):
        return None  # genuinely new file (an Eturlia class) — leave it alone
    if not os.path.exists(modified):
        sys.exit("patched file missing: " + modified)

    diff = subprocess.run(["git", "diff", "--no-index", "--no-color", "-U3", vanilla, modified],
                          capture_output=True, text=True).stdout
    if "@@" not in diff:
        sys.exit("no hunks for " + rel)
    hunks = diff[diff.index("@@"):]
    return ("diff --git a/%s b/%s\n" % (path_in_patch, path_in_patch)
            + "index %s..%s 100644\n" % (hash_object(vanilla), hash_object(modified))
            + "--- a/%s\n" % path_in_patch
            + "+++ b/%s\n" % path_in_patch
            + hunks)


def process(patch_path):
    text = io.open(patch_path, encoding="utf-8", newline="").read()
    out = []
    changed = 0
    # Walk the file section by section.
    idx = 0
    while True:
        start = text.find("diff --git ", idx)
        if start == -1:
            out.append(text[idx:])
            break
        out.append(text[idx:start])
        nxt = text.find("diff --git ", start + 10)
        end = nxt if nxt != -1 else len(text)
        section = text[start:end]
        if "new file mode" in section:
            header = section.split("\n", 1)[0]
            # "diff --git a/<path> b/<path>"
            path_in_patch = header.split(" b/", 1)[1].strip()
            replacement = modify_section(path_in_patch)
            if replacement is not None:
                section = replacement
                changed += 1
                print("  rewrote as modification: %s" % path_in_patch)
            else:
                print("  kept as new file (Eturlia-owned): %s" % path_in_patch)
        out.append(section)
        idx = end
    if changed:
        io.open(patch_path, "w", encoding="utf-8", newline="").write("".join(out))
    print("%s: %d section(s) rewritten" % (os.path.basename(patch_path), changed))


for arg in sys.argv[1:]:
    print("== %s" % os.path.basename(arg))
    process(arg)
