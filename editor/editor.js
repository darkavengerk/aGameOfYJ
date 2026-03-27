/**
 * 영조의나라 — GitHub Pages 웹 에디터
 *
 * 동작 방식:
 *  1. raw.githubusercontent.com 으로 카드 JSON 읽기 (인증 불필요)
 *  2. 브라우저에서 title / main_text 편집
 *  3. GitHub Contents API로 수정된 JSON 커밋 → Actions 자동 트리거
 *
 * 인증: GitHub PAT (contents:write 권한)를 sessionStorage에 저장
 *
 * 카드 스키마:
 *   표준 카드 (policy, event): { title, main_text }
 *   갑자 카드 (noron, soron):  { number, gapja_name, gan, ji, animal, element, main_text }
 */

const REPO_OWNER = 'darkavengerk';
const REPO_NAME  = 'aGameOfYJ';
const BRANCH     = 'master';
const RAW_BASE   = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}`;
const API_BASE   = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}`;

// 편집 가능한 카드 덱 목록
const EDITABLE_DECKS = [
  { label: '정책 카드',    file: 'data/cards/policy_cards.json', type: 'standard' },
  { label: '사건 카드',    file: 'data/cards/event_cards.json',  type: 'standard' },
  { label: '노론 60갑자',  file: 'data/cards/noron_gapja.json',  type: 'gapja'    },
  { label: '소론 60갑자',  file: 'data/cards/soron_gapja.json',  type: 'gapja'    },
];

// ── 상태 ─────────────────────────────────────────────────────
let _token   = '';
let _deck    = null;   // { meta, data, file }
let _cardIdx = -1;
let _dirty   = false;

// ── DOM 참조 ──────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── 초기화 ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  _token = sessionStorage.getItem('gh_pat') || '';
  _initNav();
  _initDeckSelect();
  _route();
  window.addEventListener('hashchange', _route);
});

function _route() {
  const hash = location.hash || '#/editor';
  if (hash.startsWith('#/settings')) {
    _showSettings();
  } else {
    _showEditor();
    if (!_token) { _setStatus('error', 'GitHub PAT가 필요합니다. 설정 화면에서 입력해 주세요.'); return; }
    if (!_deck)  { _loadDeck(0); }
  }
}

// ── 네비게이션 ────────────────────────────────────────────────
function _initNav() {
  $('nav-editor').addEventListener('click', () => { location.hash = '#/editor'; });
  $('nav-settings').addEventListener('click', () => { location.hash = '#/settings'; });
  $('save-token-btn').addEventListener('click', _saveToken);
  $('clear-token-btn').addEventListener('click', _clearToken);
}

function _showEditor() {
  $('editor-view').classList.remove('hidden');
  $('settings-view').classList.add('hidden');
  $('nav-editor').classList.add('active');
  $('nav-settings').classList.remove('active');
}

function _showSettings() {
  $('settings-view').classList.remove('hidden');
  $('editor-view').classList.add('hidden');
  $('nav-settings').classList.add('active');
  $('nav-editor').classList.remove('active');
  $('token-input').value = _token;
}

// ── PAT 관리 ─────────────────────────────────────────────────
function _saveToken() {
  const t = $('token-input').value.trim();
  if (!t) { alert('토큰을 입력해 주세요.'); return; }
  _token = t;
  sessionStorage.setItem('gh_pat', t);
  _setStatus('ok', 'PAT 저장 완료. 에디터로 이동합니다.');
  setTimeout(() => { location.hash = '#/editor'; _loadDeck(0); }, 800);
}

function _clearToken() {
  _token = '';
  sessionStorage.removeItem('gh_pat');
  $('token-input').value = '';
  _setStatus('ok', 'PAT 삭제 완료.');
}

// ── 덱 선택 ──────────────────────────────────────────────────
function _initDeckSelect() {
  const sel = $('deck-select');
  EDITABLE_DECKS.forEach((d, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = d.label;
    sel.appendChild(opt);
  });
  sel.addEventListener('change', () => {
    if (_dirty && !confirm('저장하지 않은 변경이 있습니다. 계속할까요?')) {
      sel.value = EDITABLE_DECKS.findIndex(d => d.file === _deck?.file) ?? 0;
      return;
    }
    _loadDeck(parseInt(sel.value, 10));
  });
}

async function _loadDeck(deckIdx) {
  const meta = EDITABLE_DECKS[deckIdx];
  if (!meta) return;

  _setStatus('busy', `${meta.label} 로드 중…`);
  try {
    const res  = await fetch(`${RAW_BASE}/${meta.file}?t=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    _deck    = { meta, data, file: meta.file };
    _cardIdx = -1;
    _dirty   = false;

    _renderCardList();
    $('editor-placeholder').classList.remove('hidden');
    $('card-form-wrap').classList.add('hidden');
    _setStatus('ok', `${meta.label} 로드 완료 (${data.cards.length}장)`);
  } catch (e) {
    _setStatus('error', `로드 실패: ${e.message}`);
  }
}

// ── 카드 목록 렌더링 ──────────────────────────────────────────
function _cardLabel(card) {
  if (card.gapja_name) return `${card.number}. ${card.gapja_name} (${card.animal})`;
  return card.title || '(제목 없음)';
}

function _renderCardList() {
  const list = $('card-list');
  list.innerHTML = '';
  (_deck?.data?.cards ?? []).forEach((card, i) => {
    const el = document.createElement('div');
    el.className = 'card-list-item' + (i === _cardIdx ? ' selected' : '');
    el.textContent = _cardLabel(card);
    el.addEventListener('click', () => _selectCard(i));
    list.appendChild(el);
  });
}

// ── 카드 선택 / 폼 렌더링 ────────────────────────────────────
function _selectCard(idx) {
  if (_dirty && !confirm('저장하지 않은 변경이 있습니다. 계속할까요?')) return;
  _cardIdx = idx;
  _dirty   = false;
  _renderCardList();
  _renderForm(_deck.data.cards[idx]);
  $('editor-placeholder').classList.add('hidden');
  $('card-form-wrap').classList.remove('hidden');
}

function _renderForm(card) {
  const isGapja = _deck.meta.type === 'gapja';

  // 갑자 카드용 읽기 전용 정보
  $('gapja-info').classList.toggle('hidden', !isGapja);
  if (isGapja) {
    $('f-gapja-info').textContent =
      `${card.number}번 | ${card.gapja_name} | ${card.gan}${card.ji} | ${card.animal} | ${card.element}`;
  }

  // 제목 — 갑자 카드는 읽기 전용
  $('title-row').classList.toggle('hidden', isGapja);
  if (!isGapja) $('f-title').value = card.title ?? '';

  // main_text — 구 형식(flavor_text)도 폴백으로 지원
  $('f-main-text').value = card.main_text ?? card.flavor_text ?? '';
}

// ── 공개 에디터 API ───────────────────────────────────────────
const editor = {
  markDirty() { _dirty = true; },

  addCard() {
    if (!_deck || _deck.meta.type === 'gapja') {
      alert('갑자 카드는 추가할 수 없습니다.');
      return;
    }
    const newCard = { title: '새 카드', main_text: '' };
    _deck.data.cards.push(newCard);
    _renderCardList();
    _selectCard(_deck.data.cards.length - 1);
  },

  deleteCard() {
    if (_cardIdx < 0 || !confirm('이 카드를 삭제할까요?')) return;
    _deck.data.cards.splice(_cardIdx, 1);
    _cardIdx = -1;
    _dirty   = false;
    _renderCardList();
    $('editor-placeholder').classList.remove('hidden');
    $('card-form-wrap').classList.add('hidden');
  },

  discardChanges() {
    if (!confirm('변경 사항을 취소할까요?')) return;
    _dirty = false;
    _renderForm(_deck.data.cards[_cardIdx]);
  },

  async publish() {
    if (!_token) {
      _setStatus('error', 'GitHub PAT가 필요합니다. 설정 화면에서 입력해 주세요.');
      return;
    }
    if (_cardIdx >= 0) { _collectForm(); }

    $('publish-btn').disabled = true;
    _setStatus('busy', '커밋 중…');

    try {
      // 1. 현재 SHA 가져오기
      const infoRes = await fetch(`${API_BASE}/contents/${_deck.file}`, {
        headers: { Authorization: `Bearer ${_token}` },
      });
      if (!infoRes.ok) throw new Error(`SHA 조회 실패: HTTP ${infoRes.status}`);
      const { sha } = await infoRes.json();

      // 2. 수정된 JSON을 커밋
      const updated = JSON.stringify(_deck.data, null, 2);
      const b64     = btoa(unescape(encodeURIComponent(updated)));

      const putRes = await fetch(`${API_BASE}/contents/${_deck.file}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `에디터: ${_deck.meta.label} 수정`,
          content: b64,
          sha,
          branch: BRANCH,
        }),
      });
      if (!putRes.ok) {
        const err = await putRes.json().catch(() => ({}));
        throw new Error(err.message || `HTTP ${putRes.status}`);
      }

      _dirty = false;
      _setStatus('busy', '커밋 완료 — 빌드 대기 중…');
      _pollBuildStatus();
    } catch (e) {
      _setStatus('error', `발행 실패: ${e.message}`);
    } finally {
      $('publish-btn').disabled = false;
    }
  },
};

// ── 폼 → 카드 객체 수집 ──────────────────────────────────────
function _collectForm() {
  const card    = _deck.data.cards[_cardIdx];
  const isGapja = _deck.meta.type === 'gapja';

  if (!isGapja) {
    card.title = $('f-title').value.trim();
  }
  card.main_text = $('f-main-text').value.trim();
  // 구 형식 필드 제거 (마이그레이션)
  delete card.flavor_text;
  delete card.id;
  delete card.cost;
  delete card.effects;
  delete card.trigger;
  delete card.tags;

  _renderCardList();
  _dirty = false;
}

// ── 빌드 상태 polling ────────────────────────────────────────
async function _pollBuildStatus() {
  const MAX_POLLS = 40;
  const INTERVAL  = 5000;

  for (let i = 0; i < MAX_POLLS; i++) {
    await _sleep(INTERVAL);
    try {
      const res = await fetch(`${API_BASE}/actions/runs?per_page=1`, {
        headers: { Authorization: `Bearer ${_token}` },
      });
      const { workflow_runs } = await res.json();
      if (!workflow_runs?.length) continue;

      const run = workflow_runs[0];
      if (run.status === 'completed') {
        if (run.conclusion === 'success') {
          _setStatus('ok', '빌드 완료! GitHub Pages가 갱신됩니다.');
        } else {
          _setStatus('error', `빌드 실패 (conclusion: ${run.conclusion})`);
        }
        return;
      }
      _setStatus('busy', `빌드 진행 중… (${run.status})`);
    } catch (_) { /* 무시하고 polling 계속 */ }
  }
  _setStatus('ok', '발행 완료. 빌드 상태는 GitHub Actions에서 확인하세요.');
}

function _sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── 상태 바 ──────────────────────────────────────────────────
function _setStatus(level, msg) {
  $('status-dot').className  = `status-dot ${level}`;
  $('status-text').textContent = msg;
}

window.editor = editor;
