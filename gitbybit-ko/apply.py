#!/usr/bin/env python3
"""GitByBit 레슨 한글화 패치.

정품으로 설치한 GitByBit 익스텐션의 스페인어 로케일 슬롯에 한국어 번역을 얹는다.
번역 텍스트만 바꾸며, git 명령/옵션/파일명 같은 코드 조각은 건드리지 않는다.

사용법:
    python3 apply.py            적용
    python3 apply.py --revert   원상복구
"""
import glob, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 번역 대상 컴포넌트 — 산문만. Cm/Git/Arg/Opt/Cr(명령·인자·옵션·브랜치)은 의도적으로 제외한다.
TRANSLATE = {"p","strong","Continue","GitopediaEntry","div","Title","em","Goal","GoalSummary",
             "figcaption","b","li","a","Fragment","h1","h2","h3","h4","i","blockquote","Tip",
             "TitleList","Note","Quiz","Task","Section","WebOnly","VSCodeOnly","Windows","Linux",
             "MacOS","NonWindows","strike","Panel","Skip","ChapterRoadmap"}
SPAN_OK = re.compile(r'^(Skip to|sloppy|optional|SKIPPED HERE\?|Meow!|Chapter \d+:.*)$')
CALL = re.compile(r'\(0,([\w$]+)\.(jsxs?)\)\(([A-Za-z_$][\w.$]*|"[a-z0-9]+"),\{')
ATTR = re.compile(r'\b(chapter|question|title|alt):"((?:[^"\\]|\\.)+)"')


def _skip_string(s, i, q):
    """여는 따옴표 위치 i 에서 닫는 따옴표 위치를 돌려준다."""
    j = i + 1
    n = len(s)
    while j < n and s[j] != q:
        j += 2 if s[j] == '\\' else 1
    return j


def match_close(s, i):
    """s[i] 가 여는 괄호일 때 짝이 맞는 닫는 괄호 위치를 돌려준다."""
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c in '"\'`':
            j = _skip_string(s, j, c) + 1
            continue
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return n - 1


def children_spans(blk, i):
    """속성 블록을 균형 맞춰 훑어 children 문자열들의 (시작, 끝)을 모은다.

    children 이 문자열이면 그 하나, 배열이면 최상위 원소 문자열 전부.
    배열을 보지 않으면 'A ', <strong>, ' B' 로 쪼개진 문장을 통째로 놓친다.
    """
    depth, n, out, await_kids = 1, len(blk), [], False
    while i < n and depth:
        c = blk[i]
        if c in '"\'':
            j = _skip_string(blk, i, c)
            if await_kids:
                out.append((i + 1, j)); await_kids = False
            i = j + 1; continue
        if c == '`':
            i = _skip_string(blk, i, '`') + 1; continue
        if blk.startswith("children:", i):
            i += 9
            if i < n and blk[i] == '[':
                d, j = 1, i + 1
                while j < n and d:
                    ch = blk[j]
                    if ch in '"\'`':
                        k = _skip_string(blk, j, ch)
                        if d == 1 and ch == '"':
                            out.append((j + 1, k))
                        j = k + 1; continue
                    if ch in '[({': d += 1
                    elif ch in '])}': d -= 1
                    j += 1
                i = j
            else:
                await_kids = True
            continue
        if c in '{([': depth += 1
        elif c in '})]': depth -= 1
        i += 1
    return out


def find_ext():
    pats = ["~/.vscode/extensions/gitbybit.gitbybit-*",
            "~/.vscode-insiders/extensions/gitbybit.gitbybit-*",
            "~/.cursor/extensions/gitbybit.gitbybit-*"]
    hits = [d for p in pats for d in glob.glob(os.path.expanduser(p)) if os.path.isdir(d)]
    if not hits:
        sys.exit("GitByBit 익스텐션을 찾을 수 없다. VS Code 마켓플레이스에서 먼저 설치할 것.")
    return sorted(hits)[-1]


def one(pattern, where):
    hits = glob.glob(os.path.join(where, pattern))
    if len(hits) != 1:
        sys.exit(f"예상과 다른 파일 구성이다 ({pattern}: {len(hits)}개). 지원 버전은 1.5.x.")
    return hits[0]


def resolve(blk):
    """번들러가 1글자로 줄인 변수명을 원래 컴포넌트/태그 이름으로 되돌린다."""
    names = {}
    for m in re.finditer(r'let ([A-Za-z_$][\w$]*)=\{((?:[a-z0-9]+:"[a-z0-9]+",)+)', blk):
        for tag, val in re.findall(r'([a-z0-9]+):"([a-z0-9]+)"', m.group(2)):
            names[f"{m.group(1)}.{tag}"] = val
    for m in re.finditer(r'\{((?:[A-Z][\w]*:[A-Za-z_$][\w$]*,?)+)\}=[A-Za-z_$]', blk):
        for comp, var in re.findall(r'([A-Z][\w]*):([A-Za-z_$][\w$]*)', m.group(1)):
            names[var] = comp
    return names


def translate(src, ko):
    """번역 대상 위치에서만 치환한다. 같은 문자열이라도 코드 자리면 그대로 둔다."""
    ends = [m.end() for m in re.finditer(r";return Component;[`\']," + r"[A-Za-z_$]{1,3}=Object\.freeze", src)]
    starts, out, hit = [0] + ends, [], 0
    for i, end in enumerate(ends):
        blk = src[starts[i]:end]
        nm = resolve(blk)
        edits = []
        for m in CALL.finditer(blk):
            raw = m.group(3)
            if raw.startswith('"'):
                real = raw.strip('"')          # "p" 는 HTML 태그 리터럴이지 변수가 아니다
            else:
                real = nm.get(raw) or raw.split('.')[-1]
            if not (real in TRANSLATE or real == "span"):
                continue
            for a, b in children_spans(blk, m.end()):
                v = blk[a:b]
                if real == "span" and not SPAN_OK.match(v):
                    continue
                if v in ko:                      # 빈 문자열도 유효한 번역이다 (조각 삭제)
                    edits.append((a, b, ko[v]))
        for m in ATTR.finditer(blk):
            k, v = m.group(1), m.group(2)
            if k == "chapter" and re.match(r'^\d\d/', v): continue
            if k == "title" and re.match(r'^[\w./-]+$', v): continue
            if v in ko:
                edits.append((m.start(2), m.end(2), ko[v]))
        edits.sort(key=lambda e: -e[0])
        seen = set()
        for a, b, rep in edits:
            if a in seen: continue
            seen.add(a)
            blk = blk[:a] + rep + blk[b:]
            hit += 1
        out.append(blk)
    out.append(src[ends[-1]:])
    return "".join(out), hit


def main():
    ext = find_ext()
    assets = os.path.join(ext, "vscode-frontend", "assets")
    en = one("en/content-gitbybit-part1-*.js", assets)
    es = one("es/content-gitbybit-part1-*.js", assets)
    pkg = os.path.join(ext, "vscode-backend", "packages.js")
    # 언어 선택 UI(사이드바 드롭다운·로드맵)는 webview 번들에 로케일 목록 사본을
    # 따로 갖고 있다. packages.js 만 고치면 백엔드는 맞아도 화면(webview)은
    # 그대로 스페인어로 남는다 — 실제로 이 사본을 놓쳐서 한 번 재작업했다.
    router = one("content-*.js", assets)
    i18n = one("es/i18n-*.js", assets)
    print(f"익스텐션: {os.path.basename(ext)}")

    if "--revert" in sys.argv:
        n = 0
        for f in (es, pkg, router, i18n):
            if os.path.exists(f + ".bak"):
                shutil.copyfile(f + ".bak", f); n += 1
        print(f"복구 완료 ({n}개 파일). VS Code 를 재시작할 것." if n else "복구할 백업이 없다.")
        return

    for f in (es, pkg, router, i18n):          # 최초 1회만 백업 — 재적용해도 원본이 보존된다
        if not os.path.exists(f + ".bak"):
            shutil.copyfile(f, f + ".bak")

    ko = json.load(open(os.path.join(HERE, "ko.json"), encoding="utf-8"))
    bad = [k for k, v in ko.items() if re.search(r"(?<!\\)'", v)]   # \' 이스케이프는 정상
    if bad:
        sys.exit(f"이스케이프 안 된 작은따옴표가 있어 중단한다 ({len(bad)}건). 문자열이 깨진다.")

    src = open(en, encoding="utf-8").read()   # en 은 읽기 전용, 번역 결과는 es 로만 나간다
    patched, hit = translate(src, ko)
    open(es, "w", encoding="utf-8").write(patched)

    s = open(pkg + ".bak", encoding="utf-8").read()
    s = s.replace('es: { locale: "es", title: "Español" }', 'es: { locale: "es", title: "한국어" }', 1)

    sidebar = json.load(open(os.path.join(HERE, "sidebar.json"), encoding="utf-8"))
    m = re.search(r'(const META\$s = )(\{.*?\n\})(;\n)', s, re.S)
    if m:
        block = re.sub(r'"((?:[^"\\]|\\.)+)"',
                        lambda mm: f'"{sidebar.get(mm.group(1), mm.group(1))}"', m.group(2))
        s = s[:m.start(2)] + block + s[m.end(2):]

    courses = json.load(open(os.path.join(HERE, "courses.json"), encoding="utf-8"))
    s = re.sub(r'"es": "((?:[^"\\]|\\.)+)"',
                lambda mm: f'"es": "{courses.get(mm.group(1), mm.group(1))}"', s)
    open(pkg, "w", encoding="utf-8").write(s)

    r = open(router + ".bak", encoding="utf-8").read()
    r = r.replace('es:{locale:"es",title:"Español"}', 'es:{locale:"es",title:"한국어"}', 1)

    # webview 로드맵이 쓰는 레슨 메타(title/title_plain/chapter) 사본 — packages.js 의
    # META$s 와 동일한 데이터지만 이 파일에 통째로 다시 박혀 있다 (Dt 변수).
    i = r.find('Dt={"01/0000-introduction-to-version-control"')
    if i >= 0:
        start = r.index("{", i)
        end = match_close(r, start)
        block = re.sub(r'"((?:[^"\\]|\\.)*)"',
                        lambda mm: f'"{sidebar.get(mm.group(1), mm.group(1))}"', r[start:end + 1])
        r = r[:start] + block + r[end + 1:]

    # 코스 제목 객체(6개) — {en:"...",es:"...","pt-br":"...",ru:"...",uk:"..."}
    r = re.sub(r'(\{en:"(?:[^"\\]|\\.)*",es:)"((?:[^"\\]|\\.)*)"(,"pt-br")',
               lambda mm: mm.group(1) + f'"{courses.get(mm.group(2), mm.group(2))}"' + mm.group(3), r)
    open(router, "w", encoding="utf-8").write(r)

    # 세 번째 사본: webview UI 문자열 카탈로그(해시 키 -> ["문자열"]). 이미 가진
    # 번역과 겹치는 것만 안전하게 채운다 — 여기서 새 번역을 만들지는 않는다.
    ii = open(i18n + ".bak", encoding="utf-8").read()
    combo = {**sidebar, **courses}
    ii = re.sub(r'\["((?:[^"\\]|\\.)*)"\]',
                lambda mm: f'["{combo[mm.group(1)]}"]' if mm.group(1) in combo else mm.group(0), ii)
    open(i18n, "w", encoding="utf-8").write(ii)

    print(f"번역 적용: {hit}곳 / 사전 {len(ko)}건")
    print("VS Code 에서 'Developer: Reload Window' 후, GitByBit 언어 목록에서 '한국어'를 고를 것.")


if __name__ == "__main__":
    main()
