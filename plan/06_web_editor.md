# 05 — GitHub Pages 웹 에디터 + 발행 시스템

## 핵심 질문

> GitHub Pages에서 카드 텍스트 편집 + 발행 버튼이 가능한가?

**결론: 완전히 가능하다.** 단, 동작 방식을 이해해야 한다.

---

## GitHub Pages의 기술적 한계

GitHub Pages는 **순수 정적 파일 호스팅**이다. 서버 사이드 코드가 없다.

| 불가능한 것 | 대안 |
|-------------|------|
| 서버에서 Python 실행 | GitHub Actions (클라우드 실행) |
| 파일 직접 저장 | GitHub Contents API (브라우저에서 직접 커밋) |
| 사용자 인증 관리 | GitHub Personal Access Token (PAT) |

즉, **"저장" 기능은 브라우저가 GitHub API를 직접 호출해서 처리한다.**

---

## 전체 흐름

```
[브라우저 — GitHub Pages]
  1. data/cards/policy_cards.json 을 GitHub Raw API로 읽어옴
  2. 편집기 UI에서 카드 텍스트 수정
  3. 발행 버튼 클릭
       ↓
  4. GitHub Contents API로 수정된 JSON을 master에 직접 커밋
       ↓
  5. push 이벤트 → GitHub Actions 자동 트리거
       ↓
  6. build.py 실행 → 이미지 재생성 → deploy/ 커밋
       ↓
  7. GitHub Pages 자동 갱신
```

브라우저 → GitHub API → Actions → Pages 사이클이 완결된다.
별도 서버, Heroku, Lambda 등이 전혀 필요 없다.

---

## 라우팅 — GitHub Pages에서 SPA 가능한가?

가능하다. 두 가지 방법:

### 방법 A: 해시 라우팅 (추천, 구현 쉬움)
```
https://darkavengerk.github.io/aGameOfYJ/#/editor
https://darkavengerk.github.io/aGameOfYJ/#/cards/policy
https://darkavengerk.github.io/aGameOfYJ/#/board
```
JavaScript에서 `window.location.hash`를 읽어 화면을 전환.
별도 설정 없이 즉시 동작.

### 방법 B: 경로 라우팅 + 404.html 핵
```
https://darkavengerk.github.io/aGameOfYJ/editor
```
`404.html`에 리다이렉트 스크립트를 넣어 `index.html`로 보내는 방식.
URL이 더 깔끔하지만 설정이 필요하고 SEO에 영향 없음(어차피 비공개 도구).

→ **해시 라우팅이 간단하고 충분하다.**

---

## 인증 — PAT (Personal Access Token)

브라우저에서 GitHub API를 호출하려면 인증 토큰이 필요하다.

### 방법: PAT를 브라우저에 저장

1. GitHub Settings → Developer settings → Personal access tokens 에서 발급
   - 필요 권한: `contents: write`, `actions: write`
2. 편집기 최초 실행 시 토큰 입력 UI 표시
3. `sessionStorage` 또는 `localStorage`에 저장
4. 이후 모든 API 호출에 `Authorization: Bearer <token>` 헤더 사용

**보안:**
- PAT는 코드에 절대 포함하지 않는다 (공개 레포이므로 노출되면 즉시 폐기됨)
- 개인 프로젝트이므로 자신이 발급한 토큰을 자신의 브라우저에 저장하는 건 실용적
- 토큰을 잊어버려도 새로 발급하면 됨 — 편집기가 토큰 입력 화면으로 안내

---

## GitHub API 호출 구조

### 카드 데이터 읽기

```javascript
// raw.githubusercontent.com으로 직접 읽기 (인증 불필요)
const res = await fetch(
  'https://raw.githubusercontent.com/darkavengerk/aGameOfYJ/master/data/cards/policy_cards.json'
);
const data = await res.json();
```

### 카드 데이터 저장 (커밋)

```javascript
// 현재 파일의 SHA 먼저 가져오기
const fileRes = await fetch(
  'https://api.github.com/repos/darkavengerk/aGameOfYJ/contents/data/cards/policy_cards.json',
  { headers: { Authorization: `Bearer ${token}` } }
);
const { sha } = await fileRes.json();

// 수정된 내용을 base64로 인코딩해서 커밋
await fetch(
  'https://api.github.com/repos/darkavengerk/aGameOfYJ/contents/data/cards/policy_cards.json',
  {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: '편집기: 카드 내용 수정',
      content: btoa(unescape(encodeURIComponent(JSON.stringify(updatedData, null, 2)))),
      sha,                // 충돌 방지용 현재 SHA
    }),
  }
);
```

이 커밋이 master에 push되면 GitHub Actions가 자동 트리거된다.
별도 workflow_dispatch 호출이 필요 없다.

### 빌드 상태 확인

```javascript
// 가장 최근 Actions 실행 상태 polling
const runs = await fetch(
  'https://api.github.com/repos/darkavengerk/aGameOfYJ/actions/runs?per_page=1',
  { headers: { Authorization: `Bearer ${token}` } }
);
const { workflow_runs } = await runs.json();
const status = workflow_runs[0].status; // queued | in_progress | completed
```

발행 버튼 클릭 후 "빌드 중..." 인디케이터 표시 → 완료되면 미리보기 링크 안내.

---

## 편집기 UI 구성

### 화면 구조 (해시 라우팅)

```
/#/              ← 기존 미리보기 페이지 (현재 index.html)
/#/editor        ← 편집기 메인
/#/editor/cards  ← 카드 목록
/#/editor/board  ← 보드 섹션 편집
/#/settings      ← 토큰 설정
```

### 카드 편집 화면

```
┌─────────────────────────────────────────┐
│ 카드 타입: [policy_cards ▼]             │
├──────────────┬──────────────────────────┤
│ 카드 목록    │ 탕평책                   │
│              │ ─────────────────────── │
│ ▶ 탕평책     │ 제목:  [탕평책        ] │
│   규장각 설치│ 비용:  영향력 [1      ] │
│   군제 개혁  │ 효과:  영향력 [2      ] │
│   대동법 실시│ 설명:  [당파 간 균형을  │
│              │         맞춰 정국...   ] │
│ [+ 카드 추가]│ 특수:  [없음 ▼]         │
│              │                         │
│              │    [취소]  [발행]        │
└──────────────┴──────────────────────────┘
```

### 구현 스택

- **Vanilla JS + 최소한의 라이브러리** 권장
  - 빌드 도구 없이 GitHub Pages에 바로 배포 가능
  - `editor/index.html`, `editor/editor.js`, `editor/editor.css` 3개 파일로 구성 가능
- 또는 **Vue 3 CDN** (`<script src="https://unpkg.com/vue@3">`) — 빌드 없이 컴포넌트 기반 UI
- React/Next.js는 빌드 파이프라인이 추가로 필요해서 오버엔지니어링

---

## 구현 순서

### Phase 1: 기초 (1~2일)
1. `editor/index.html` 생성 — 토큰 입력 + 기본 레이아웃
2. 카드 데이터 읽기 (raw GitHub API)
3. 카드 목록 표시 + 텍스트 편집 폼

### Phase 2: 저장 (1일)
4. GitHub Contents API로 JSON 커밋
5. 발행 후 빌드 상태 polling + 완료 알림

### Phase 3: 편의 기능 (1~2일)
6. 카드 추가 / 삭제
7. 보드 섹션 편집 (03_board_system.md 와 연계)
8. 변경사항 preview (이미지 실제 렌더링은 불가하지만 텍스트 미리보기)

---

## 주의사항

### 동시 편집 충돌

두 브라우저(예: 휴대폰 + PC)에서 동시에 편집하면 SHA 불일치로 두 번째 저장이 실패한다.
→ 개인 프로젝트이므로 큰 문제는 아님. 에러 메시지를 명확하게 안내하면 충분.

### 빌드 시간

현재 CI 빌드는 120장 전부 재생성 → 약 1~3분 소요.
02_build_pipeline.md의 증분 빌드가 완료되면 텍스트 1장 수정 시 10초 이내로 단축 가능.

### GitHub API Rate Limit

인증된 요청은 시간당 5,000회. 편집기 사용량으로는 절대 초과되지 않음.
