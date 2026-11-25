#!/usr/bin/env python3
"""Build the downloadable PDF ebook from the Markdown guides.

Requirements:  pip install markdown playwright   (uses the installed Google Chrome)
Usage:         python3 tools/build_ebook.py
Output:        ebook/CCNA-Packet-Tracer-Labs.pdf
"""
import datetime
import html
import os
import re
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'ebook')
HTML_OUT = os.path.join(OUT_DIR, 'ebook.html')
PDF_OUT = os.path.join(OUT_DIR, 'CCNA-Packet-Tracer-Labs.pdf')
TITLE = 'CCNA Hands-On Labs with Cisco Packet Tracer'

LABS = [
    'lab01-pt-intro-basic-config', 'lab02-ipv4-subnetting-ipv6', 'lab03-vlans-intervlan-routing',
    'lab04-stp-etherchannel-port-security', 'lab05-static-routing-ospf', 'lab06-dhcp-nat-acl-capstone',
]

# (part label, chapter title override or None, markdown file)
CHAPTERS = [('Getting Started', 'Introduction', 'README.md'),
            ('Getting Started', 'Syllabus', 'SYLLABUS.md'),
            ('Getting Started', None, 'docs/packet-tracer-quickstart.md')]
CHAPTERS += [('Lab Guides', None, f'labs/{lab}/README.md') for lab in LABS]
CHAPTERS += [('Appendices', 'Appendix A – IOS Command Cheat Sheet', 'docs/ios-command-cheatsheet.md'),
             ('Appendices', 'Appendix B – Lab Report Template', 'docs/lab-report-template.md'),
             ('Appendices', 'Appendix C – Instructor Guide', 'docs/instructor-guide.md')]

CSS = r"""
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt;
       line-height: 1.45; color: #1f2328; margin: 0; }
h1, h2, h3, h4 { color: #13548f; line-height: 1.25; page-break-after: avoid; break-after: avoid; }
h1 { font-size: 21pt; border-bottom: 3px solid #13548f; padding-bottom: 6px; margin: 0 0 14px; }
h2 { font-size: 14.5pt; margin: 22px 0 8px; border-bottom: 1px solid #d0d7de; padding-bottom: 3px; }
h3 { font-size: 11.5pt; margin: 16px 0 6px; color: #1f2328; }
h4 { font-size: 10.5pt; margin: 12px 0 4px; color: #1f2328; }
p { margin: 6px 0; }
a { color: #0969da; text-decoration: none; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.6pt; background: #f2f4f7; padding: 1px 4px;
       border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #d0d7de; border-left: 4px solid #2b7bc4; border-radius: 4px;
      padding: 8px 10px; white-space: pre-wrap; word-break: break-word; margin: 8px 0; }
pre code { background: none; padding: 0; font-size: 8.3pt; line-height: 1.35; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 8.8pt;
        page-break-inside: auto; }
tr { page-break-inside: avoid; break-inside: avoid; }
th { background: #13548f; color: #fff; text-align: left; font-weight: 600; }
th, td { border: 1px solid #c9d1d9; padding: 4px 6px; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f8fa; }
blockquote { margin: 8px 0; padding: 6px 12px; background: #eef6ff; border-left: 4px solid #54aeff;
             border-radius: 3px; page-break-inside: avoid; break-inside: avoid; }
blockquote p { margin: 3px 0; }
ul, ol { margin: 4px 0 6px; padding-left: 22px; }
li { margin: 2px 0; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 14px 0; }
img { max-width: 100%; display: block; margin: 8px auto; page-break-inside: avoid; }
.chapter { page-break-before: always; break-before: page; }
.part { page-break-before: always; break-before: page; display: flex; flex-direction: column;
        justify-content: center; height: 240mm; text-align: center; }
.part .label { font-size: 11pt; letter-spacing: 3px; text-transform: uppercase; color: #57606a; }
.part .name { font-size: 32pt; font-weight: 700; color: #13548f; margin-top: 10px; }
.details-title { font-weight: 700; color: #8a4600; margin-top: 10px; }
/* cover */
.cover { height: 255mm; display: flex; flex-direction: column; justify-content: space-between;
         background: linear-gradient(160deg, #0d3f6e 0%, #13548f 55%, #2b7bc4 100%); color: #fff;
         padding: 28mm 18mm 18mm; margin: -2mm; border-radius: 4px; }
.cover .kicker { font-size: 12pt; letter-spacing: 4px; text-transform: uppercase; opacity: .85; }
.cover h1 { color: #fff; border: none; font-size: 36pt; margin: 12px 0 8px; padding: 0; }
.cover .sub { font-size: 15pt; opacity: .95; }
.cover .facts { display: flex; gap: 14px; margin-top: 26px; }
.cover .fact { background: rgba(255,255,255,.14); border-radius: 8px; padding: 10px 16px; }
.cover .fact b { display: block; font-size: 22pt; }
.cover .foot { font-size: 9.5pt; opacity: .9; line-height: 1.6; }
.cover img { margin: 18px 0 0; background: #fff; border-radius: 6px; padding: 4px; }
/* toc */
.toc h1 { page-break-before: always; break-before: page; }
.toc ol { list-style: none; padding: 0; }
.toc .tpart { font-weight: 700; color: #57606a; text-transform: uppercase; letter-spacing: 1.5px;
              font-size: 9pt; margin: 14px 0 4px; }
.toc .tch { font-size: 11pt; font-weight: 600; margin: 5px 0 2px; }
.toc .tsub { font-size: 9.3pt; color: #57606a; margin: 1px 0 1px 18px; }
.toc a { color: inherit; }
"""

MD_EXT = ['tables', 'fenced_code', 'sane_lists', 'attr_list']


def slug(text, prefix):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return f'{prefix}-{s}'[:80]


def preprocess(md, base_dir):
    # images -> absolute file URLs
    def img(m):
        path = os.path.normpath(os.path.join(base_dir, m.group(2)))
        return f'<img alt="{html.escape(m.group(1))}" src="file://{path}">'
    md = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', img, md)
    # relative links -> plain text (external links stay)
    md = re.sub(r'\[([^\]]+)\]\((?!https?://)([^)]+)\)', r'\1', md)
    # <details> blocks are always expanded in print
    md = re.sub(r'<summary>(.*?)</summary>',
                lambda m: '<p class="details-title">' + re.sub(r'</?b>', '', m.group(1)) + '</p>', md)
    md = md.replace('<details>', '<div class="details" markdown="1">\n').replace('</details>', '\n</div>')
    return md


def chapter_html(idx, title_override, rel):
    path = os.path.join(ROOT, rel)
    md = preprocess(open(path, encoding='utf-8').read(), os.path.dirname(path))
    body = markdown.markdown(md, extensions=MD_EXT + ['md_in_html'])
    prefix = f'c{idx}'
    toc = []
    first = True

    def head(m):
        nonlocal first
        level, text = int(m.group(1)), m.group(2)
        plain = html.unescape(re.sub(r'<[^>]+>', '', text))
        if level == 1 and first:
            first = False
            shown = title_override or plain
            toc.append((1, shown, prefix))
            return f'<h1 id="{prefix}">{html.escape(shown)}</h1>'
        hid = slug(plain, prefix)
        if level == 2:
            toc.append((2, plain, hid))
        return f'<h{level} id="{hid}">{text}</h{level}>'
    body = re.sub(r'<h([1-4])>(.*?)</h\1>', head, body)
    return f'<section class="chapter">{body}</section>', toc


def build_html():
    os.makedirs(OUT_DIR, exist_ok=True)
    parts, toc_entries, last_part = [], [], None
    for i, (part, title, rel) in enumerate(CHAPTERS):
        if part != last_part:
            pid = f'part-{len(toc_entries)}'
            parts.append(f'<section class="part" id="{pid}"><div class="label">Part</div>'
                         f'<div class="name">{html.escape(part)}</div></section>')
            toc_entries.append(('part', part, pid))
            last_part = part
        body, toc = chapter_html(i, title, rel)
        # the part divider already starts a page
        if parts[-1].startswith('<section class="part"'):
            body = body.replace('<section class="chapter">', '<section class="chapter" style="'
                                'page-break-before:always">', 1)
        parts.append(body)
        toc_entries += [('ch' if lvl == 1 else 'sub', t, a) for lvl, t, a in toc]

    toc_html = ['<section class="toc"><h1 id="toc">Contents</h1>']
    for kind, text, anchor in toc_entries:
        cls = {'part': 'tpart', 'ch': 'tch', 'sub': 'tsub'}[kind]
        if kind == 'sub' and not re.match(r'(Period \d+|Objectives|Review Questions|Troubleshooting)', text):
            continue
        toc_html.append(f'<div class="{cls}"><a href="#{anchor}">{html.escape(text)}</a></div>')
    toc_html.append('</section>')

    cover_img = os.path.join(ROOT, 'labs', LABS[5], 'images', 'topology.svg')
    today = datetime.date.today().strftime('%B %Y')
    cover = f'''
<section class="cover">
  <div>
    <div class="kicker">Cisco CCNA 200-301 · Practical Lab Course</div>
    <h1>{TITLE}</h1>
    <div class="sub">Step-by-step guides, topologies, solution configs and answer keys</div>
    <div class="facts">
      <div class="fact"><b>6</b>sessions</div>
      <div class="fact"><b>30</b>periods</div>
      <div class="fact"><b>8.2</b>Packet Tracer</div>
    </div>
    <img src="file://{cover_img}" alt="Lab 6 topology">
  </div>
  <div class="foot">Every lab was built and tested end-to-end in Cisco Packet Tracer 8.2.2.<br>
  Source: github.com/hoanglvh/ccna-packet-tracer-labs · Edition {today}</div>
</section>'''

    # appendix D/E: answer keys and solution configs
    extra = ['<section class="part"><div class="label">Part</div><div class="name">Solutions</div></section>']
    toc_extra = [('part', 'Solutions', 'part-solutions')]
    extra[0] = extra[0].replace('class="part"', 'class="part" id="part-solutions"', 1)
    ans = ['# Appendix D – Answer Keys']
    cfg = ['# Appendix E – Solution Configurations',
           'Final configuration of every device. Paste into the device CLI after `enable` and '
           '`configure terminal` to build a reference topology quickly.']
    for n, lab in enumerate(LABS, 1):
        sol = os.path.join(ROOT, 'labs', lab, 'solutions')
        a = open(os.path.join(sol, 'answers.md'), encoding='utf-8').read()
        a = re.sub(r'^# (.*)$', r'## \1', a, count=1, flags=re.M)
        a = re.sub(r'^## (?!Lab)', '### ', a, flags=re.M)
        ans.append(a)
        cfg.append(f'## Lab {n:02d}')
        for f in sorted(os.listdir(sol)):
            if f.endswith('.txt'):
                cfg.append(f'### {f[:-4]}\n\n```\n' + open(os.path.join(sol, f), encoding='utf-8').read().rstrip()
                           + '\n```')
            elif f.endswith('.md') and f != 'answers.md':
                t = open(os.path.join(sol, f), encoding='utf-8').read()
                cfg.append(re.sub(r'^# (.*)$', r'### \1', t, count=1, flags=re.M))
    for idx, md_text in ((90, '\n\n'.join(ans)), (91, '\n\n'.join(cfg))):
        tmp = os.path.join(OUT_DIR, f'_tmp{idx}.md')
        open(tmp, 'w', encoding='utf-8').write(md_text)
        body, toc = chapter_html(idx, None, os.path.relpath(tmp, ROOT))
        os.remove(tmp)
        if len(extra) == 1:
            body = body.replace('<section class="chapter">', '<section class="chapter" style="'
                                'page-break-before:always">', 1)
        extra.append(body)
        toc_extra += [('ch' if lvl == 1 else 'sub', t, a) for lvl, t, a in toc]
    for kind, text, anchor in toc_extra:
        cls = {'part': 'tpart', 'ch': 'tch', 'sub': 'tsub'}[kind]
        if kind == 'sub':
            continue
        toc_html.insert(-1, f'<div class="{cls}"><a href="#{anchor}">{html.escape(text)}</a></div>')

    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{TITLE}</title>'
           f'<style>{CSS}</style></head><body>{cover}{"".join(toc_html)}{"".join(parts)}{"".join(extra)}'
           f'</body></html>')
    os.makedirs(OUT_DIR, exist_ok=True)
    open(HTML_OUT, 'w', encoding='utf-8').write(doc)
    return HTML_OUT


def render_pdf(html_path):
    from playwright.sync_api import sync_playwright
    footer = ('<div style="width:100%;font-size:8px;color:#57606a;padding:0 16mm;display:flex;'
              'justify-content:space-between;font-family:Helvetica,Arial,sans-serif">'
              f'<span>{TITLE}</span><span><span class="pageNumber"></span> / '
              '<span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome')
        page = browser.new_page()
        page.goto('file://' + html_path, wait_until='networkidle')
        page.pdf(path=PDF_OUT, format='A4', print_background=True, display_header_footer=True,
                 header_template='<span></span>', footer_template=footer, outline=True, tagged=True,
                 margin={'top': '16mm', 'bottom': '18mm', 'left': '14mm', 'right': '14mm'})
        browser.close()
    return PDF_OUT


if __name__ == '__main__':
    h = build_html()
    pdf = render_pdf(h)
    if '--keep-html' not in sys.argv:
        os.remove(h)
    print('wrote', os.path.relpath(pdf, ROOT))
