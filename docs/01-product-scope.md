# Escopo do Produto

## Visão geral

O produto é uma plataforma de dados versionados para flashcards de concursos
públicos. Seu foco é armazenar, revisar, versionar e distribuir cartões para
uso no Anki.

## Responsabilidades

### Catálogo de flashcards

Cada cartão possui identidade estável, taxonomia controlada, versão atual e
histórico completo.

Além do UUID interno, cada cartão possui um `public_id` único e imutável,
visível ao usuário e pesquisável na plataforma.

### Versionamento

Alterações pedagógicas criam novas versões. Versões publicadas são imutáveis e
permanecem disponíveis para auditoria.

### Curadoria

Cartões podem ser cadastrados manualmente ou importados por uma integração.
Todo conteúdo passa por validação e revisão antes da publicação.

Usuários podem reportar uma versão publicada. Cada report gera uma tarefa de
revisão administrativa. A decisão é auditável e pode:

```text
rejected
duplicate
converted_to_new_version
```

Uma conversão cria uma nova versão em `needs_review`. Ela não altera a versão
reportada, não muda automaticamente `current_version_id` e não atualiza decks.

### Decks e releases

Cartões publicados são organizados em decks. Cada publicação gera uma release
imutável contendo ações explícitas:

```text
added
updated
removed
deprecated
```

### Exportação para Anki

Uma release pode ser exportada em CSV. A exportação deve incluir identificadores
estáveis para permitir rastreamento e futuras atualizações:

```text
card_id
public_id
card_version_id
deck_id
front_text
back_text
answer_text
explanation_text
tags
```

O formato exato poderá ser configurável, mas a identidade nunca deve depender
do texto do cartão.

### Sincronização incremental

Clientes autenticados podem listar releases e consultar somente os deltas
posteriores à última release aplicada localmente. A sincronização preserva:

```text
card_id
public_id
old_card_version_id
new_card_version_id
action
release_number
```

As mudanças são aplicadas sequencialmente. O sistema não acessa o banco interno
do Anki e não armazena o progresso de revisão do usuário.

Endpoint conceitual:

```text
GET /cards/public/{public_id}
```

A consulta pública retorna apenas cartões publicados. Rascunhos e versões em
revisão exigem acesso administrativo.

### Interface administrativa

Uma interface administrativa simples será construída depois da preparação do
backend para produção. Seu objetivo será permitir:

- adicionar cartões;
- consultar cartões e seu histórico;
- modificar conteúdo por meio de uma nova versão;
- aprovar e publicar versões;
- organizar cartões em decks;
- publicar releases;
- baixar o CSV para importação no Anki.

A interface consumirá exclusivamente a API. Ela não acessará o PostgreSQL
diretamente e não permitirá edição de uma versão publicada.

## Fora do escopo

- processamento de PDFs;
- OCR;
- extração de provas ou questões;
- geração de flashcards por IA;
- embeddings e RAG;
- sincronização direta com o banco interno do Anki;
- agendamento de revisão ou progresso do estudante;
- aplicativo móvel.
- edição colaborativa em tempo real;
- construtor visual avançado de templates do Anki na primeira interface.

## Integrações futuras

Um gerador externo ou add-on do Anki poderá consumir APIs autenticadas. Esses
clientes nunca acessam diretamente o banco nem alteram versões publicadas.
