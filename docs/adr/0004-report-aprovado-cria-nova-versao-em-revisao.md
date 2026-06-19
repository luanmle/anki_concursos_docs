# ADR-0004 — Report aprovado cria nova versão em revisão, não publica diretamente

**Status:** Aceito
**Data:** 2026-06-12

## Contexto

Quando um aluno abre um report (erro no cartão) e o admin decide corrigi-lo (`decision=converted_to_new_version`), o conteúdo corrigido precisa passar pelo mesmo ciclo de qualidade dos cartões criados manualmente — evitando que conteúdo não revisado chegue ao aluno.

## Decisão

`ReportService._create_resulting_version` cria `CardVersion` com `status=CardVersionStatus.NEEDS_REVIEW` (`app/services/reports.py:187-201`). A nova versão entra no fluxo normal de curadoria: precisa ser aprovada e publicada em uma release antes de chegar ao aluno.

O `ReviewTask.resulting_card_version_id` referencia a nova versão criada, permitindo rastrear qual correção originou qual versão.

Regra extra: reports do tipo `outdated_law` com decisão `converted_to_new_version` exigem `evidence_reviewed=true` antes de serem aceitos (`app/services/reports.py:131-146`).

## Consequências

- **Positivas:** conteúdo corrigido passa por aprovação antes de ser publicado; relatório de report preserva rastreabilidade da correção.
- **Negativas:** fluxo é mais lento — uma correção de typo exige aprovação + release para chegar ao aluno.
- **Neutras:** `CardReport` e `ReviewTask` são imutáveis após encerramento (`app/models/entities.py:758-808`).

## Alternativas consideradas

- **Publicar diretamente na decisão do admin:** descartado para manter consistência com o ciclo de qualidade e evitar conteúdo errado distribuído sem revisão.
