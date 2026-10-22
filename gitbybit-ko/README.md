# GitByBit 본코스 한글 패치

GitByBit(VS Code Git 학습 익스텐션) 본코스 50과를 한국어로 읽기 위한 패치다.
**번역 텍스트만** 담고 있고 익스텐션 자체는 들어 있지 않다. 각자 마켓플레이스에서 정품을 설치한 뒤 적용한다.

## 적용

```bash
# 1. VS Code 마켓플레이스에서 GitByBit 설치 (1.5.x)
# 2. VS Code 를 완전히 종료
# 3. 패치 적용
python3 apply.py
```

적용 후 VS Code 를 열고 `Developer: Reload Window` → GitByBit 사이드바 → 언어 목록에서 **한국어** 선택.

## 되돌리기

```bash
python3 apply.py --revert
```

## 동작 방식

익스텐션에는 로케일 5종(en/es/pt-br/ru/uk)의 레슨이 전부 로컬 파일로 들어 있고 구조가 서로 같다.
이 패치는 **스페인어 슬롯에 한국어를 덮어쓴다.** 언어 목록의 "Español" 자리가 "한국어"가 된다.

한국어 슬롯을 새로 만들지 않은 이유는 그렇게 하면 콘텐츠 라우터의 매핑 157개를 손대야 하기 때문이다.
대신 스페인어로는 학습할 수 없게 된다.

## 번역 범위

- 본코스 50과 전체 (`content-gitbybit-part1`) — 문자열 1,706건 / 적용 2,243곳
- Gitopedia 66항목과 연습 41과는 **원문 그대로** 둔다

다음은 의도적으로 번역하지 않는다. 번역하면 실습이 깨지거나 화면과 달라진다.

| 대상 | 예 |
|---|---|
| git 명령·옵션·인자 | `git commit` `--amend` `.git` |
| 브랜치명·경로 | `main` `origin` `~/project` |
| git 실제 출력 | `Changes not staged for commit:` |
| 코드 블록 안 파일 내용 | `This is a bug!` |
| 커밋 메시지 예시 | `Linked styles to hello.html` |
| VS Code UI 라벨 | `View` `Terminal` `SOURCE CONTROL` |

git 명령어·옵션·브랜치명·파일 경로는 번역 대상에서 제외된다.
`git commit --amend` 가 한국어로 바뀌면 실습이 불가능하기 때문에, 컴포넌트 종류를 보고 산문만 골라 치환한다.

## 주의

- 익스텐션이 업데이트되면 패치가 사라진다. `apply.py` 를 다시 돌리면 된다.
- GitByBit 은 All Rights Reserved 제품이다. 이 패치는 **각자 정품 설치본을 각자 고치는** 용도이며,
  개조한 익스텐션을 다시 배포하지 말 것.
- Pro 기능·라이선스·인증에는 손대지 않는다.
