#!/usr/bin/env python3
"""Bangun versi bahasa lain (folder en/, jp/) dari halaman Bahasa Indonesia.

Pakai:  python3 tools/i18n/build.py
        1. Menyambungkan pemilih bahasa di halaman ID (EN -> en/<halaman>, JP -> jp/<halaman>).
        2. Untuk setiap bahasa di LANGS, menulis <folder>/<halaman> dengan teks dari
           tools/i18n/<folder>.json, path aset ke ../, atribut lang, dan pemilih bahasa
           yang aktif di bahasa tersebut.
Teks yang belum punya terjemahan dibiarkan dalam Bahasa Indonesia dan dilaporkan.
Jalankan extract.py lebih dulu bila halaman ID berubah.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import ATTRS, JS_STR, LANGS, ROOT, pages  # noqa: E402

TOKENS = re.compile(r"(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<svg\b[^>]*>.*?</svg>|<[^>]+>)", re.S | re.I)
ATTR = re.compile(r'(\s(?:' + "|".join(ATTRS) + r')=")([^"]*)(")')
SW_ITEM = re.compile(r'<a\b[^>]*LanguageSwitcher-module__mfObaG__item\b[^>]*>(?:(?!</a>).)*?itemCode">(ID|EN|JP)</span>', re.S)
ACTIVE_CLS = " LanguageSwitcher-module__mfObaG__itemActive"
TRIGGER = re.compile(r'(<button\b[^>]*LanguageSwitcher-module__mfObaG__trigger(?:Desktop|Mobile)[^>]*>)(<img\b[^>]*>)ID<')
ASSET_PATH = re.compile(r"""(?<=["'(=\s,])(?:\./)?(assets/|vendor/|support\.js)""")
# Bendera tombol pemilih bahasa: desktop memakai images/flags, mobile memakai blob
FLAG_ID = ("assets/images/flags/indonesia.svg", "assets/blob/26256cb7a05aa69de4bd1e3d88679a2a.svg")
FLAGS = {
    "en": ("assets/images/flags/united-states.svg", "assets/blob/2ccdd48cd09134a9214f5c231d1ba9e3.svg"),
    "jp": ("assets/images/flags/japan.svg", "assets/blob/33b489436a6170625eea9521ea58422d.svg"),
}
HTML_LANG = {"en": "en", "jp": "ja"}
# Teks tanpa huruf tidak masuk kamus; tanda baca yang berdiri sendiri (mis. titik setelah link) diganti di sini
PUNCT = {"jp": {".": "。"}}
# CSS tambahan per bahasa; auto-phrase memotong baris Jepang di batas frasa, bukan di tengah kata.
# overflow-wrap:anywhere menjaga frasa yang terlalu panjang tetap bisa dipotong (mis. di sel grid sempit).
EXTRA_CSS = {"jp": "<style>:lang(ja) :is(h1,h2,h3,h4,p,li,figcaption,label,legend,span){word-break:auto-phrase;overflow-wrap:anywhere}</style>"}
INDEX_LINK = {"en": "Open Home", "jp": "ホームを開く"}


def set_href(item, href):
    return re.sub(r'href="[^"]*"', 'href="%s"' % href, item, count=1)


def set_active(item, on):
    item = item.replace('aria-current="page" ', "").replace(ACTIVE_CLS, "")
    if on:
        item = item.replace("<a ", '<a aria-current="page" ', 1)
        item = item.replace("LanguageSwitcher-module__mfObaG__item", "LanguageSwitcher-module__mfObaG__item" + ACTIVE_CLS, 1)
    return item


def switcher(html, page, lang):
    """Atur href dan status aktif item ID/EN/JP di pemilih bahasa ("id" = halaman sumber)."""
    up = "" if lang == "id" else "../"

    def fix(m):
        item, code = m.group(0), m.group(1).lower()
        target = page if code == "id" else code + "/" + page
        item = set_href(item, target if lang == "id" else (page if code == lang else up + target))
        return set_active(item, code == lang)
    return SW_ITEM.sub(fix, html)


def translate(html, tr, missing):
    def text(t):
        key = t.strip()
        if not key or key not in tr:
            return t
        if not tr[key]:
            missing.add(key)
            return t
        return t.replace(key, tr[key], 1)

    def attrs(tag):
        return ATTR.sub(lambda m: m.group(1) + text(m.group(2)) + m.group(3), tag)

    def js(script):
        head_end = script.index(">") + 1
        head, body = script[:head_end], script[head_end:]
        if "src=" in head:
            return script

        def lit(m):
            q = m.group(0)[0]
            inner = next(g for g in m.groups() if g is not None)
            new = text(inner)
            if new == inner:
                new = attrs(inner)
            if new == inner:
                return m.group(0)
            return q + new.replace("\\", "\\\\").replace(q, "\\" + q) + q
        return head + JS_STR.sub(lit, body)

    out = []
    for part in TOKENS.split(html):
        if not part:
            continue
        low = part[:7].lower()
        if low.startswith("<script"):
            out.append(js(part))
        elif low.startswith("<style") or low.startswith("<svg"):
            out.append(part)
        elif part.startswith("<"):
            out.append(attrs(part))
        else:
            out.append(text(part))
    return "".join(out)


def localize(html, page, lang, tr, missing):
    html = translate(html, tr, missing)
    html = html.replace('<html lang="id">', '<html lang="%s">' % HTML_LANG[lang], 1)
    if lang in EXTRA_CSS:
        html = html.replace("</head>", EXTRA_CSS[lang] + "</head>", 1)
    html = switcher(html, page, lang)
    html = TRIGGER.sub(lambda m: m.group(1) + m.group(2) + lang.upper() + "<", html)
    for a, b in zip(FLAG_ID, FLAGS[lang]):
        html = re.sub(r'(LanguageSwitcher-module__mfObaG__trigger(?:Desktop|Mobile)[^>]*><img\b[^>]*src=")' + re.escape(a), r"\g<1>" + b, html)
    return ASSET_PATH.sub(r"../\1", html)


def main():
    sources = {}
    for page in pages():
        src = os.path.join(ROOT, page)
        with open(src, encoding="utf-8") as f:
            html = f.read()
        linked = switcher(html, page, "id")
        if linked != html:
            with open(src, "w", encoding="utf-8") as f:
                f.write(linked)
        sources[page] = linked
    for lang in LANGS:
        with open(os.path.join(ROOT, "tools", "i18n", lang + ".json"), encoding="utf-8") as f:
            tr = json.load(f)
        tr.update(PUNCT.get(lang, {}))
        out = os.path.join(ROOT, lang)
        os.makedirs(out, exist_ok=True)
        total = set()
        for page, html in sources.items():
            missing = set()
            with open(os.path.join(out, page), "w", encoding="utf-8") as f:
                f.write(localize(html, page, lang, tr, missing))
            total |= missing
            if missing:
                print(f"{lang}/{page}: {len(missing)} teks belum diterjemahkan")
        with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
            f.write('<!doctype html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                    '<meta http-equiv="refresh" content="0; url=Main.dc.html"><title>Nadesco</title></head>'
                    '<body><a href="Main.dc.html">%s</a></body></html>\n' % (HTML_LANG[lang], INDEX_LINK[lang]))
        print(f"{lang}/: {len(sources)} halaman, {len(total)} teks unik belum diterjemahkan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
