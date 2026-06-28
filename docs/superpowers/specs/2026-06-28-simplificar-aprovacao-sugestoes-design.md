# Design — Simplificar aprovação de sugestões (1 clique)

**Data:** 2026-06-28
**Status:** aprovado para implementação (aguardando revisão do spec)
**Branch de design:** `design/simplify-suggestion-approval`

## Problema

O fluxo atual de aceitar uma sugestão de nota é longo e espalhado por 3 telas
(~5 cliques):

1. `/admin/suggestions` → **Aceitar** (cria `CardVersion` em `needs_review`)
2. card → **Aprovar** versão → **Publicar** versão
3. deck → **Atualizar versão** → **Publicar release**

Só depois a nota muda no baralho. O usuário considera os passos demais e a
**segunda revisão desnecessária** para sugestões.

## Decisão

Aceitar uma sugestão de **card** passa a fazer tudo em **uma ação**, server-side:

1. cria a `CardVersion` já com `status=published` (sem etapa `needs_review`/approve);
2. **bumpa** todos os decks ativos que contêm o card para essa versão;
3. **publica uma release** em cada deck afetado.

Resultado: a nota atualiza imediatamente no sync/baralho. Zero telas extras.

Rejeitar continua igual (só muda `status`).

### Decisões de produto (confirmadas)

- **Até a nota no baralho** — o 1 clique vai do aceite até a release.
- **Todos os decks** — se o card está em vários decks ativos, bumpa + publica
  release em cada um.
- **1 aceite = N releases** (1 por deck afetado). Releases podem acumular; sem
  agrupamento (aceitável).
- **Escopo: só sugestões.** Reports (denúncias) mantêm o ADR-0004
  (`needs_review`). Este design não toca no fluxo de reports.

## Casos de borda

Aceitar **não** auto-publica nestes casos — apenas marca `accepted` (a UI avisa
que nenhuma versão foi publicada):

- **Só tags** (`new_tags`/`updated_tags` sem mudança de campo) — não há novo
  conteúdo de card para versionar.
- **Nota nova** (sugestão de deck, `card_id` nulo) — criar um card novo a partir
  da sugestão é uma feature separada, fora deste escopo.
- **Exclusão** (`delete`) — remoção de card do deck permanece manual.
- **`content_hash` idêntico** ao de uma versão existente — no-op (não cria
  versão duplicada), marca aceita.

## Arquitetura

### Backend

Substitui `NoteSuggestionService._create_review_version` por uma orquestração
`_apply_accepted_suggestion(suggestion, reviewed_by)` chamada dentro de
`review()` quando `status == accepted` e nenhuma `resulting_card_version_id` foi
informada.

Passos, na mesma unidade de trabalho:

1. Carrega o card publicado + versão publicada atual (base para campos não
   tocados).
2. Mapeia `suggestion.fields` (nomes Anki) → `front/back/answer/explanation` por
   heurística (igual à atual: Front/Text→front, Back/Extra→back, Answer→answer,
   Explanation→explanation; campos ausentes herdam a base).
3. Se nada mapeável mudou, ou `content_hash` já existe → retorna `None` (no-op).
4. Cria `CardVersion(status=published)`, com `version_number` seguinte e
   `content_hash`; atualiza `card.current_version_id` e `card.status=published`.
5. Para cada `DeckCard` ativo (`removed_at IS NULL`) do card: atualiza
   `card_version_id` para a nova versão.
6. Para cada deck afetado: cria uma `Release` + `ReleaseItem`s do estado atual
   (reusa a lógica de release já existente em `DeckService`/repositório).
7. Grava `suggestion.resulting_card_version_id` = id da nova versão.

**Reuso vs. duplicação:** preferir extrair a lógica de criação de release de
`DeckService.publish_release` para um helper reutilizável (repositório/serviço)
em vez de duplicar. Detalhe fica para o plano de implementação.

**Imutabilidade:** criar uma versão já `published` é permitido (os
eventos/triggers bloqueiam *modificar/excluir* versões publicadas, não criar).
Releases continuam imutáveis após criadas.

### Frontend

- `SuggestionCard`: botão **"Aceitar"** → **"Aceitar e publicar"**; mensagem de
  sucesso "Publicada no baralho". Remover o CTA "Abrir cartão para aprovar e
  publicar" (não é mais necessário).
- Telas de card (`CardDetailPage`) e deck (`DeckPages`) permanecem inalteradas —
  continuam disponíveis para edição/curadoria manual (ex.: reports, nova versão
  manual). As ações por versão e "Atualizar versão" continuam úteis fora do
  fluxo de sugestão.

### ADR

Novo **ADR-0007 — Sugestão aceita publica direto (supera ADR-0004 para
sugestões)**. Registra: para `note_suggestions`, aceitar cria versão publicada e
release sem segunda revisão; reports seguem o ADR-0004.

## Arquivos afetados (previsão)

- `app/services/suggestions.py` — orquestração de aceite-e-publica.
- `app/repositories/suggestions.py` — helpers de versão/release (ou reuso de
  `DeckRepository`).
- `app/services/decks.py` / `app/repositories/decks.py` — extrair helper de
  release se for reusar.
- `admin/src/components/suggestions/SuggestionCard.tsx` — rótulo/CTA/sucesso.
- `docs/adr/0007-*.md` — novo ADR.
- Testes: `tests/test_suggestions_api.py`.

## Testes (comportamentos)

- Aceitar sugestão de card → cria versão **published** (não needs_review), card
  `current_version` = nova, e existe nova release no deck contendo a versão.
- Card em 2 decks → ambos bumpam e ganham release.
- Só-tags / nota-nova / delete → aceita sem criar versão/release.
- `content_hash` idêntico → no-op (sem versão duplicada), aceita.
- Rejeitar → sem versão/release.
- Sync (`since_release=0`) do deck retorna o campo novo após o aceite.

## Fora de escopo

- Mudar o fluxo de reports.
- Criar card a partir de sugestão de nota nova.
- Agrupar várias sugestões numa única release.
- Remoção automática de card no `delete`.
