"""원본 시험지 PDF로부터 로컬 전용 자료를 만든다.

  python build.py --src "원본 PDF들이 있는 폴더"

만들어지는 것 (모두 .gitignore 대상):
  pages/    : 시험지 각 면 JPG  — 뷰어에서 시험지를 옆에 띄워 보기 위한 것
  pdf/      : 원본 시험지 + 답지 합본 PDF
저장소에 들어가는 solutions/(풀이만 PDF)는 --sol 옵션으로 다시 만들 수 있다.
"""
import argparse, io, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = r'C:/Windows/Fonts'          # 맑은 고딕 (다른 OS면 한글 TTF 폴더로 바꿀 것)
CSS = """
@font-face{font-family:mg;src:url(malgun.ttf)} @font-face{font-family:mg;src:url(malgunbd.ttf);font-weight:bold}
*{font-family:mg;font-size:9.5pt;line-height:1.45}
h1{font-size:14pt;color:#b8322a;margin:0 0 6pt}
.q{margin:0 0 8pt}
.n{font-weight:bold;color:#fff;background-color:#b8322a;padding:1pt 4pt}
.a{font-weight:bold;color:#b8322a;font-size:10.5pt}
.w{color:#222}
.note{color:#7a5b00;font-size:8.5pt}
img{width:300pt}
"""


def answer_pdf(exam, arch, out_path):
    import pymupdf
    html = f"<h1>{exam['title']} — 답 및 풀이</h1>"
    for q in exam['qs']:
        html += (f"<div class='q'><span class='n'>{q['q']}</span> <span class='a'>답: {q['a']}</span>"
                 + (f"<br/><span class='w'>{q['w']}</span>" if q['w'] else '')
                 + (f"<br/><img src='{q['fig']}'/>" if q.get('fig') else '') + "</div>")
    story = pymupdf.Story(html=html, user_css=CSS, archive=arch)
    buf = io.BytesIO()
    w = pymupdf.DocumentWriter(buf)
    mb = pymupdf.paper_rect('a4'); where = mb + (36, 36, -36, -36)
    more = 1
    while more:
        dev = w.begin_page(mb); more, _ = story.place(where); story.draw(dev); w.end_page()
    w.close()
    d = pymupdf.open('pdf', buf.getvalue()); d.subset_fonts()
    d.save(out_path, garbage=3, deflate=True); d.close()


def main():
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='..', help='원본 시험지 PDF 폴더')
    ap.add_argument('--sol', action='store_true', help='풀이만 PDF(solutions/)도 다시 생성')
    a = ap.parse_args()

    data = json.loads(open(os.path.join(BASE, 'data.js'), encoding='utf-8').read().partition('=')[2].rstrip().rstrip(';'))
    arch = pymupdf.Archive(); arch.add(pymupdf.Archive(FONT)); arch.add(pymupdf.Archive(os.path.join(BASE, 'figs')))
    for d in ('pages', 'pdf', 'solutions'):
        os.makedirs(os.path.join(BASE, d), exist_ok=True)

    missing = []
    for e in data:
        tmp = os.path.join(BASE, 'solutions', e['id'] + '.pdf')
        if a.sol or not os.path.exists(tmp):
            answer_pdf(e, arch, tmp)

        src = os.path.join(a.src, e['file'])
        if not os.path.exists(src):
            missing.append(e['file']); continue

        doc = pymupdf.open(src)
        for i, page in enumerate(doc, 1):                      # pages/
            pix = page.get_pixmap(dpi=110)
            pix.save(os.path.join(BASE, 'pages', f"{e['id']}_p{i}.jpg"), jpg_quality=78)
        r = doc[0].rect                                        # pdf/ (합본)
        doc[0].insert_textbox(pymupdf.Rect(r.width - 200, 6, r.width - 10, 22),
                              f"답·풀이: {doc.page_count + 1}면부터", fontname='kr',
                              fontfile=os.path.join(FONT, 'malgun.ttf'), fontsize=9,
                              color=(0.72, 0.2, 0.16), align=2)
        ans = pymupdf.open(tmp); doc.insert_pdf(ans); ans.close()
        doc.subset_fonts()
        doc.save(os.path.join(BASE, 'pdf', e['id'] + '.pdf'), garbage=3, deflate=True)
        print(e['id'], e['title'])

    if missing:
        print('\n원본을 못 찾은 시험지 (--src 확인):', *missing, sep='\n  ', file=sys.stderr)


if __name__ == '__main__':
    main()
