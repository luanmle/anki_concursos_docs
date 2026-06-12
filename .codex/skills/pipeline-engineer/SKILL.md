---
name: pipeline-engineer
description: Orienta o fluxo de cadastro, versionamento, publicação, releases e exportação CSV de flashcards, sem processamento de documentos ou IA.
---
# pipeline-engineer

## Propósito

Implementar ou revisar o fluxo que transforma cartões cadastrados em releases
e arquivos CSV reproduzíveis para o Anki.

## Fluxo

```text
create_card
→ validate_card
→ review_card_version
→ publish_card_version
→ attach_to_deck
→ publish_release
→ export_release_csv
```

## Regras

1. Criar cartão e versão 1 em uma transação.
2. Não editar versão publicada.
3. Gerar nova versão para alteração pedagógica.
4. Publicar apenas versões aprovadas.
5. Tornar releases imutáveis.
6. Exportar conteúdo da versão registrada na release.
7. Incluir IDs estáveis no CSV.
8. Produzir CSV determinístico em UTF-8.
9. Registrar falhas de exportação quando usar `processing_jobs`.
10. Não implementar PDF, OCR, IA, embeddings ou RAG.

## Idempotência

- Não duplicar versão com o mesmo conteúdo.
- Não publicar duas releases com o mesmo número no deck.
- A mesma release e configuração devem gerar o mesmo hash.

## Checklist

- O `card_id` permaneceu estável?
- A versão antiga foi preservada?
- A release contém apenas versões publicadas?
- O CSV corresponde à release?
- Aspas, delimitadores e quebras de linha foram testados?
