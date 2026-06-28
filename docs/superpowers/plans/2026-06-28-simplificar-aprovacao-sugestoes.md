# Simplificar aprovação de sugestões — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer "Aceitar" uma sugestão de card publicar a mudança em 1 ação (cria versão publicada + bumpa decks + publica release), sem segunda revisão.

**Architecture:** A orquestração vive em `NoteSuggestionService` e **sequencia serviços já existentes e testados** — cria a `CardVersion` (needs_review) via repo, transiciona com `CardService.approve_version`/`publish_version`, e para cada deck com o card chama `DeckService.add_card` (bump) + `DeckService.publish_release`. Nada de release/versão é reimplementado.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic; pytest (SQLite em memória); React + vitest.

## Global Constraints

- Escopo: **apenas sugestões**. Reports mantêm ADR-0004 (`needs_review`). Não tocar `app/services/reports.py`.
- Sem migration (nenhuma mudança de schema).
- Mapeamento Anki→4 campos por heurística: `Front/Text→front_text`, `Back/Extra→back_text`, `Answer→answer_text`, `Explanation→explanation_text`; campos ausentes herdam a versão publicada.
- No-op (só marca `accepted`, sem versão/release) quando: `card_id` nulo, sugestão só de tags, tipo `delete`, nada mapeável mudou, ou `content_hash` idêntico a versão existente.
- Best-effort entre serviços (cada um comita): aceitar, em caso de falha tardia, pode deixar versão publicada sem release — aceitável; registrar via `notify_exception` já usado nos serviços.
- Comitar com frequência. `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` nos commits.

---

### Task 1: Repositório — decks ativos que contêm um card

**Files:**
- Modify: `app/repositories/suggestions.py`
- Test: `tests/test_suggestions_api.py`

**Interfaces:**
- Produces: `NoteSuggestionRepository.decks_with_active_card(card_id: uuid.UUID) -> list[uuid.UUID]` — ids de decks com `DeckCard` ativo (`removed_at IS NULL`) do card, sem duplicatas.

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/test_suggestions_api.py` (usa helper `add_card_to_deck` já existente):

```python
def test_decks_with_active_card_lists_only_active(session: Session) -> None:
    deck = create_published_deck(session)
    card, version = create_published_card(session)
    add_card_to_deck(session, deck, card, version)
    repo = NoteSuggestionRepository(session)
    assert repo.decks_with_active_card(card.id) == [deck.id]
    # card sem deck → vazio
    other_card, _ = create_published_card(session)
    assert repo.decks_with_active_card(other_card.id) == []
```

Garanta o import no topo do arquivo de teste: `from app.repositories import NoteSuggestionRepository` (já existe).

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_suggestions_api.py::test_decks_with_active_card_lists_only_active -v`
Expected: FAIL com `AttributeError: ... 'decks_with_active_card'`.

- [ ] **Step 3: Write minimal implementation**

Em `app/repositories/suggestions.py`, adicionar método na classe `NoteSuggestionRepository` (perto de `add_card_version`):

```python
    def decks_with_active_card(self, card_id: uuid.UUID) -> list[uuid.UUID]:
        rows = self.session.scalars(
            select(DeckCard.deck_id)
            .where(DeckCard.card_id == card_id, DeckCard.removed_at.is_(None))
            .distinct()
        )
        return list(rows)
```

(`DeckCard` e `select` já estão importados neste arquivo.)

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_suggestions_api.py::test_decks_with_active_card_lists_only_active -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/repositories/suggestions.py tests/test_suggestions_api.py
git commit -m "feat(suggestions): repo helper decks_with_active_card

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Serviço — aceitar publica versão + release (substitui needs_review)

**Files:**
- Modify: `app/services/suggestions.py`
- Test: `tests/test_suggestions_api.py`

**Interfaces:**
- Consumes: `NoteSuggestionRepository.decks_with_active_card` (Task 1); `NoteSuggestionRepository.{get_published_card, card_version_hashes, add_card_version, next_card_version_number}` (já existem); `calculate_content_hash` (já importado); `CardService.{approve_version, publish_version}`; `DeckService.{add_card, publish_release}`.
- Produces: `NoteSuggestionService._publish_from_suggestion(suggestion, reviewed_by) -> uuid.UUID | None` — cria versão **publicada** a partir do diff, bumpa+publica release nos decks do card, retorna o id da versão (ou `None` em no-op). `review()` passa a chamá-lo no aceite.

- [ ] **Step 1: Write the failing tests**

Substituir os testes `test_accept_card_suggestion_creates_needs_review_version` por comportamento publicado e adicionar cobertura de release/edge. Em `tests/test_suggestions_api.py`:

```python
def test_accept_card_suggestion_publishes_version_and_release(session: Session) -> None:
    from app.models import Release
    user = create_user(session)
    deck = create_published_deck(session)
    card, version = create_published_card(session)
    add_card_to_deck(session, deck, card, version)
    created = service(session).create_for_card(
        card.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.CONTENT_ERROR,
            fields={"Front": {"old": "Frente original", "new": "Frente corrigida"}},
            comment="Corrige a frente.",
        ),
        user,
    )

    reviewed = service(session).review(
        created.suggestion_id,
        NoteSuggestionReviewRequest(status=NoteSuggestionStatus.ACCEPTED),
        reviewed_by="rev@example.com",
    )

    assert reviewed.status == NoteSuggestionStatus.ACCEPTED
    new_version = session.get(CardVersion, reviewed.resulting_card_version_id)
    assert new_version.status == CardVersionStatus.PUBLISHED       # publicada, não needs_review
    assert new_version.front_text == "Frente corrigida"
    refreshed_card = session.get(Card, card.id)
    assert refreshed_card.current_version_id == new_version.id     # virou a atual
    # deck ganhou release contendo a nova versão
    releases = session.scalars(select(Release).where(Release.deck_id == deck.id)).all()
    assert len(releases) == 1


def test_accept_tag_only_suggestion_creates_no_version(session: Session) -> None:
    user = create_user(session)
    card, _ = create_published_card(session)
    created = service(session).create_for_card(
        card.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.NEW_TAGS, added_tags=["nova"],
            comment="so tag",
        ),
        user,
    )
    reviewed = service(session).review(
        created.suggestion_id,
        NoteSuggestionReviewRequest(status=NoteSuggestionStatus.ACCEPTED),
        reviewed_by="rev@example.com",
    )
    assert reviewed.resulting_card_version_id is None
```

Adicionar no topo do teste, se ausente: `from sqlalchemy import select`.

Remover o antigo `test_accept_card_suggestion_creates_needs_review_version` (comportamento mudou) e manter `test_reject_card_suggestion_creates_no_version`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_suggestions_api.py -k "publishes_version_and_release or tag_only" -v`
Expected: FAIL (versão volta `needs_review`; sem release).

- [ ] **Step 3: Write the implementation**

Em `app/services/suggestions.py`:

Imports (ajustar o bloco existente):

```python
from app.models import CardVersion, NoteSuggestion, NoteSuggestionComment, User
from app.models.enums import CardVersionStatus, NoteSuggestionStatus
from app.repositories import NoteSuggestionRepository
from app.repositories.cards import CardRepository
from app.repositories.decks import DeckRepository
from app.schemas import (
    NoteSuggestionCommentCreateRequest,
    NoteSuggestionCommentListResponse,
    NoteSuggestionCommentResponse,
    NoteSuggestionCreateRequest,
    NoteSuggestionListResponse,
    NoteSuggestionResponse,
    NoteSuggestionReviewRequest,
)
from app.schemas.cards import CardVersionCreateRequest
from app.schemas.decks import ReleasePublishRequest
from app.services.cards import CardService, calculate_content_hash
from app.services.decks import DeckService
```

Em `review()`, trocar a chamada `self._create_review_version(...)` por `self._publish_from_suggestion(...)` (a linha que computa `resulting_id` no aceite permanece igual, só muda o nome do método).

Substituir o método `_create_review_version` inteiro por:

```python
    def _publish_from_suggestion(
        self, suggestion: NoteSuggestion, reviewed_by: str
    ) -> uuid.UUID | None:
        """Aceite de sugestão de card: cria versão publicada + release nos decks.

        ADR-0007: sugestão aceita publica direto (sem segunda revisão).
        ponytail: campos do Anki mapeados por heurística; sequencia serviços
        existentes (Card/Deck) em vez de reimplementar versão/release.
        """
        if suggestion.card_id is None:
            return None
        card = self.repository.get_published_card(suggestion.card_id)
        if card is None or card.current_version is None:
            return None
        base = card.current_version
        fields = suggestion.fields or {}

        def suggested(*names: str) -> str | None:
            for name in names:
                if name in fields:
                    value = fields[name]
                    return value.get("new", "") if isinstance(value, dict) else value
            return None

        new_fields = {
            "front_text": suggested("Front", "Text", "front_text") or base.front_text,
            "back_text": suggested("Back", "Extra", "back_text") or base.back_text,
            "answer_text": suggested("Answer", "answer_text") or base.answer_text,
            "explanation_text": suggested("Explanation", "explanation_text")
            or base.explanation_text,
        }
        if all(new_fields[key] == getattr(base, key) for key in new_fields):
            return None  # nada mapeável mudou (ex.: só tags)
        content_hash = calculate_content_hash(card_kind=card.card_kind, **new_fields)
        if content_hash in self.repository.card_version_hashes(card.id):
            return None  # versão idêntica já existe — no-op

        card_id = card.id
        deck_ids = self.repository.decks_with_active_card(card_id)

        card_service = CardService(CardRepository(self.session))
        deck_service = DeckService(DeckRepository(self.session))

        detail = card_service.create_version(
            card_id,
            CardVersionCreateRequest(
                change_reason=suggestion.comment or "Sugestão aceita",
                created_by=reviewed_by,
                **new_fields,
            ),
        )
        new_version_id = max(
            detail.versions, key=lambda v: v.version_number
        ).card_version_id
        card_service.approve_version(card_id, new_version_id)
        card_service.publish_version(card_id, new_version_id)

        for deck_id in deck_ids:
            deck_service.add_card(deck_id, card_id)
            deck_service.publish_release(
                deck_id,
                ReleasePublishRequest(
                    description=f"Sugestão aceita: {suggestion.suggestion_type.value}"
                ),
            )
        return new_version_id
```

Nota: `create_version`/`approve_version`/`publish_version`/`add_card`/`publish_release` abrem suas próprias transações; por isso `review()` deve **comitar a decisão de revisão antes** de chamar `_publish_from_suggestion`. Verificar que em `review()` o `self.session.commit()` da mudança de status ocorre antes da chamada; se hoje ele ocorre depois, mover: comitar status, depois `resulting_id = self._publish_from_suggestion(...)`, depois setar `suggestion.resulting_card_version_id` e comitar de novo.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_suggestions_api.py -v`
Expected: PASS (todos, incluindo reject e os novos).

- [ ] **Step 5: Lint + suite cheia**

Run: `.venv/bin/ruff check app tests && .venv/bin/python -m pytest -m "not postgres"`
Expected: ruff limpo; tudo passa.

- [ ] **Step 6: Commit**

```bash
git add app/services/suggestions.py tests/test_suggestions_api.py
git commit -m "feat(suggestions): accepting publishes version + release in one step

ADR-0007: suggestion accept publishes directly (no needs_review gate),
bumping every deck with the card and publishing a release.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: ADR-0007

**Files:**
- Create: `docs/adr/0007-sugestao-aceita-publica-direto.md`

- [ ] **Step 1: Write the ADR**

```markdown
# ADR-0007 — Sugestão aceita publica direto (supera ADR-0004 para sugestões)

## Contexto
O fluxo de aceitar uma `note_suggestion` exigia versão em `needs_review` +
aprovação + publicação no card + atualização e release no deck (3 telas).
Considerado burocrático para sugestões da comunidade.

## Decisão
Aceitar uma sugestão de card cria uma `CardVersion` já `published` e publica
release em todos os decks ativos que contêm o card, numa única ação
(`NoteSuggestionService._publish_from_suggestion`). Não há segunda revisão.

Escopo: **apenas sugestões**. Reports continuam sob ADR-0004 (`needs_review`).

No-op (só marca `accepted`): sugestão sem card, só de tags, `delete`, sem
mudança mapeável, ou `content_hash` idêntico.

## Consequências
- Nota atualiza imediatamente após o aceite; menos telas/cliques.
- 1 aceite pode gerar N releases (1 por deck afetado).
- Curadoria perde a segunda revisão para sugestões (decisão de produto).
- Imutabilidade preservada: cria nova versão publicada; não modifica publicadas.
```

- [ ] **Step 2: Commit**

```bash
git add docs/adr/0007-sugestao-aceita-publica-direto.md
git commit -m "docs(adr): ADR-0007 sugestão aceita publica direto

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Frontend — rótulo "Aceitar e publicar" + remover CTA

**Files:**
- Modify: `admin/src/components/suggestions/SuggestionCard.tsx`

**Interfaces:**
- Consumes: comportamento do endpoint de review já alterado (Task 2). Sem mudança de assinatura de API.

- [ ] **Step 1: Ajustar o botão e a mensagem**

Em `admin/src/components/suggestions/SuggestionCard.tsx`:

- Trocar o texto do botão de aceite de `Aceitar` para `Aceitar e publicar`.
- Remover o CTA do rodapé pós-aceite (bloco do `Link` "Abrir cartão para aprovar e publicar" e o `ArrowRight` se ficar sem uso). Manter o link "Ver cartão" do cabeçalho.

Botão (na seção `isPending`):

```tsx
            <button
              type="button"
              disabled={isReviewing}
              onClick={() => onReview('accepted', comment)}
              className={muriaePrimaryBtn}
            >
              <Check size={16} weight="bold" /> Aceitar e publicar
            </button>
```

Rodapé `else` (revisada): remover o `Link` do CTA, deixando só a linha "Revisada por …":

```tsx
        <div className="border-t border-mu-border pt-3 text-[12.5px] text-mu-muted">
          Revisada por {suggestion.reviewed_by ?? '—'}
          {suggestion.reviewed_at ? ` em ${formatDate(suggestion.reviewed_at)}` : ''}
          {suggestion.review_comment ? ` · "${suggestion.review_comment}"` : ''}
        </div>
```

Se `ArrowRight` ficar sem uso após remover o CTA, mantê-lo (ainda usado no link "Ver cartão" do cabeçalho) — confirmar via lint.

- [ ] **Step 2: Lint + build + testes**

Run (em `admin/`): `npm run lint && npx vitest run && npm run build`
Expected: lint limpo; testes passam (o teste de aceite usa `name: /aceitar/i`, que casa com "Aceitar e publicar"); build OK.

- [ ] **Step 3: Commit**

```bash
git add admin/src/components/suggestions/SuggestionCard.tsx
git commit -m "feat(admin): label 'Aceitar e publicar' e remove CTA de publicação manual

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

- **Cobertura do spec:** comportamento 1-clique (Task 2), múltiplos decks (Task 1+2, `decks_with_active_card` + loop), bordas no-op (Task 2 testes/guards), ADR (Task 3), frontend rótulo/CTA (Task 4). ✓
- **Reports intocados:** nenhuma task altera `reports.py`. ✓
- **Placeholders:** nenhum — código completo em cada step. ✓
- **Consistência de tipos:** `_publish_from_suggestion -> uuid | None` usado em `review()`; `decks_with_active_card -> list[uuid]` consumido no loop; nomes de métodos de Card/Deck conferem com as assinaturas reais. ✓
- **Atenção na execução:** confirmar a ordem de commit em `review()` (status antes da orquestração), pois os serviços reusados abrem transações próprias.
