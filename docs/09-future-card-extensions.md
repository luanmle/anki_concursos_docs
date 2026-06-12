# Extensões Futuras do Cartão

## Objetivo

Preparar o sistema para evoluir além dos 4 campos principais do cartão sem quebrar o modelo de dados, o versionamento ou a sincronização.

O MVP deve manter os seguintes campos principais em `card_versions`:

```text
front_text
back_text
answer_text
explanation_text
```

Esses campos representam o núcleo pedagógico do cartão.

## Regra principal

Não adicionar qualquer novo campo diretamente em `card_versions` apenas porque surgiu uma nova necessidade de exibição.

Antes de criar uma coluna nova, classificar a necessidade em uma destas categorias:

```text
1. Conteúdo pedagógico extra
2. Metadado de publicação
3. Metadado administrativo
4. Informação de sincronização
```

## 1. Conteúdo pedagógico extra

Exemplos:

```text
fundamento legal
trecho da fonte
mnemônico
jurisprudência
pegadinha da banca
comentário do professor
exemplo adicional
```

Usar:

```text
card_fields
- id
- card_version_id
- field_name
- field_label
- field_type
- field_value
- display_order
- is_required
- created_at
- updated_at
```

Regra:

- campos pedagógicos extras pertencem à versão do cartão;
- alteração relevante em campos pedagógicos extras deve gerar nova versão;
- não editar campo extra de uma versão publicada diretamente.

## 2. Metadados de publicação web

Exemplo:

```text
link da página web do cartão
slug
URL canônica
visibilidade da página
status da página
```

Usar:

```text
card_public_pages
- id
- card_id
- card_version_id
- slug
- canonical_path
- visibility
- status
- created_at
- updated_at
```

Recomendação:

Salvar:

```text
/cards/habeas-corpus-liberdade-locomocao
```

ou:

```text
habeas-corpus-liberdade-locomocao
```

Evitar salvar como dado principal:

```text
https://seudominio.com/cards/habeas-corpus-liberdade-locomocao
```

Motivo:

O domínio pode mudar, mas isso não deve gerar nova versão pedagógica do cartão.

## 3. Templates de cartão

No futuro, o sistema pode suportar diferentes modelos de cartão.

Usar:

```text
card_templates
- id
- name
- description
- status
- created_at
- updated_at
```

```text
card_template_fields
- id
- card_template_id
- field_name
- field_label
- field_type
- display_order
- is_required
- created_at
- updated_at
```

Exemplos:

```text
Cartão básico
Cartão jurídico
Cartão de lei seca
Cartão de jurisprudência
Cartão de questão comentada
Cartão de português
Cartão de informática
```

## 4. Regras para IA de desenvolvimento

Ao implementar novas funcionalidades, a IA deve seguir estas regras:

1. Manter `front_text`, `back_text`, `answer_text` e `explanation_text` como núcleo do MVP.
2. Não transformar URL pública em campo principal do cartão.
3. Usar `card_public_pages` para página web do cartão.
4. Usar `card_fields` para campos extras pedagógicos.
5. Usar `card_template_fields` quando houver templates oficiais.
6. Não editar conteúdo publicado sem criar nova versão.
7. Não gerar nova versão apenas por mudança de domínio, rota ou layout.
8. Gerar nova versão se o conteúdo pedagógico visível ao estudante mudar.
9. Manter `card_id` estável.
10. Manter sincronização baseada em `card_id` e `card_version_id`.

## Exemplo completo

```text
cards
- id: CARD-000123

card_versions
- id: VERSION-000456
- card_id: CARD-000123
- version_number: 1
- front_text: Qual remédio constitucional protege a liberdade de locomoção?
- back_text: Habeas corpus. Ele protege a liberdade de locomoção...
- answer_text: Habeas corpus.
- explanation_text: O habeas corpus é cabível quando alguém sofre ou se acha ameaçado...

card_fields
- card_version_id: VERSION-000456
- field_name: legal_basis
- field_label: Fundamento legal
- field_value: Art. 5º, LXVIII, da Constituição Federal.

card_public_pages
- card_id: CARD-000123
- card_version_id: VERSION-000456
- slug: habeas-corpus-liberdade-locomocao
- canonical_path: /cards/habeas-corpus-liberdade-locomocao
- visibility: public
- status: published
```

## Decisão arquitetural

O sistema deve nascer simples, mas preparado para crescer:

```text
Agora:
4 campos principais em card_versions

Depois:
card_fields para campos pedagógicos extras
card_public_pages para páginas web
card_templates para modelos oficiais de cartão
```
