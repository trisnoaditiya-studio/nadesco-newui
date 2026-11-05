#!/usr/bin/env python3
"""Kumpulkan teks Bahasa Indonesia dari halaman *.dc.html ke kamus terjemahan.

Pakai:  python3 tools/i18n/extract.py
Hasil:  tools/i18n/<bahasa>.json untuk setiap bahasa di LANGS (en.json, jp.json)
        ->  { "<teks ID>": "<terjemahan>" }
        Teks baru ditambahkan dengan nilai "" (belum diterjemahkan); terjemahan
        yang sudah ada tidak diubah. Teks yang tidak lagi dipakai dilaporkan saja.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGS = ("en", "jp")  # nama folder output = nama file kamus


def dict_path(lang):
    return os.path.join(ROOT, "tools", "i18n", lang + ".json")


ATTRS = ("alt", "aria-label", "title", "placeholder", "content", "data-video-title", "label")
SKIP_BLOCKS = re.compile(r"<(style|svg)\b[^>]*>.*?</\1>", re.S | re.I)
SCRIPT = re.compile(r"(<script\b[^>]*>)(.*?)(</script>)", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
ATTR = re.compile(r'\s(' + "|".join(ATTRS) + r')="([^"]*)"')
JS_STR = re.compile(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"|`((?:[^`\\]|\\.)*)`")
WORD = re.compile(r"[A-Za-zÀ-ÿ]{2,}")


def pages():
    return sorted(f for f in os.listdir(ROOT) if f.endswith(".dc.html"))


def is_text(t):
    t = t.strip()
    return bool(t) and bool(WORD.search(t)) and "{{" not in t


def looks_like_copy(s):
    """String JS yang kemungkinan teks tampilan, bukan selector/kode."""
    s = s.strip()
    if not is_text(s) or len(s) < 3:
        return False
    if re.search(r"[{};=]|=>|\bfunction\b|^[.#\[]|\.(webp|svg|png|jpe?g|mp4|html|css|js)\b|^https?:|^[a-z-]+:[^ ]", s):
        return False
    if re.fullmatch(r"[\w\-\[\]=\"'.#:>~+*() ,]+", s) and " " not in s:
        return False  # satu kata/selector/kelas
    return True


def strings_from(html):
    out = []
    # Atribut di seluruh dokumen (kecuali di dalam <script>)
    no_script = SCRIPT.sub(" ", html)
    for m in ATTR.finditer(no_script):
        if is_text(m.group(2)):
            out.append(m.group(2).strip())
    # Node teks di luar script/style/svg
    body = SKIP_BLOCKS.sub(" ", no_script)
    for chunk in TAG.split(body):
        if is_text(chunk):
            out.append(chunk.strip())
    # String literal di dalam script inline dan data x-dc
    for m in SCRIPT.finditer(html):
        if "src=" in m.group(1):
            continue
        for sm in JS_STR.finditer(m.group(2)):
            s = next(g for g in sm.groups() if g is not None)
            if looks_like_copy(s):
                out.append(s.strip())
            else:  # potongan HTML di dalam string, mis. aria-label tombol popup
                out.extend(a.group(2).strip() for a in ATTR.finditer(s) if is_text(a.group(2)))
    return out


def main():
    seen = []
    for p in pages():
        with open(os.path.join(ROOT, p), encoding="utf-8") as f:
            for s in strings_from(f.read()):
                if s not in seen:
                    seen.append(s)
    for lang in LANGS:
        path = dict_path(lang)
        data = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        added = [s for s in seen if s not in data]
        for s in added:
            data[s] = ""
        stale = [s for s in data if s not in seen]
        ordered = {s: data[s] for s in seen}
        ordered.update({s: data[s] for s in stale})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ordered, f, ensure_ascii=False, indent=1)
            f.write("\n")
        todo = sum(1 for s in seen if not ordered[s])
        print(f"{lang}.json: {len(seen)} teks, {len(added)} baru, {todo} belum diterjemahkan, {len(stale)} tidak dipakai lagi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
