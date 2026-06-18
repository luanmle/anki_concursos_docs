# Simplificacao de Fluxo, Explore e Community

## Objetivo

Este documento avalia uma mudanca de fluxo e design para tornar a plataforma
mais simples, fluida e orientada a decks. A proposta nao remove regras criticas
do backend e nao altera o contrato do add-on. Ela reorganiza a experiencia do
usuario para esconder complexidade editorial quando ela nao for necessaria.

Principio central:

```text
Decks sao a unidade principal para estudantes.
Cartoes/notas continuam sendo a unidade tecnica de versionamento.
Releases continuam sendo a unidade tecnica de sincronizacao.
```

## Direcao Recomendada

A interface deve migrar de uma experiencia centrada em filtros editoriais para
uma experiencia centrada em:

- explorar baralhos;
- assinar baralhos;
- visualizar notas de um baralho;
- sugerir melhorias em notas;
- administrar publicacao e revisao em uma area separada.

Essa mudanca e viavel sem comprometer muito o desenvolvimento atual porque o
backend ja possui:

- usuarios `student`, `admin`, `curator` e `reviewer`;
- decks publicados;
- assinaturas de decks;
- manifest e sync para add-on;
- reports e review tasks;
- versionamento por `card_id` e `card_version_id`;
- publicacao por releases imutaveis.

## O Que Deve Mudar Na Interface

### Nova Navegacao Principal

Para estudantes:

```text
Explore
Meus Baralhos
Conta
```

Para administradores e equipe editorial:

```text
Explore
Meus Baralhos
Administracao
Conta
```

O painel administrativo deve ficar separado visualmente da experiencia de
estudo. O estudante nao deve ver telas de criacao manual de cartoes, filtros
editoriais internos ou importacao.

## Tela Explore

### Objetivo

Permitir que estudantes encontrem baralhos disponiveis e acompanhem suas
inscricoes.

### Conteudo

Mostrar:

- campo de busca por nome ou descricao do baralho;
- baralhos disponiveis na plataforma;
- baralhos em que o usuario ja esta inscrito;
- status de inscricao;
- quantidade de notas/cartoes ativos;
- ultima release publicada;
- botao `Inscrever-se`;
- botao `Abrir baralho` para decks ja inscritos.

### Contratos Atuais

Endpoints ja existentes:

```text
GET /subscriptions/decks
GET /subscriptions
POST /subscriptions/{deck_id}
POST /subscriptions/{deck_id}/cancel
```

### Observacoes

O backend atual lista decks assinaveis com paginacao, mas nao possui busca por
texto. A primeira versao pode implementar busca client-side apenas sobre a
pagina carregada ou adicionar busca no backend depois.

Recomendacao:

```text
MVP: listar e filtrar localmente a pagina atual.
Futuro: adicionar query `search` ao endpoint `/subscriptions/decks`.
```

## Tela Deck

### Objetivo

Ser a pagina publica/logada do baralho. Ela deve explicar o baralho, mostrar as
notas e servir como ponte para comunidade, sugestoes e add-on.

### Conteudo

Mostrar:

- nome do baralho;
- descricao;
- status de inscricao do usuario;
- quantidade de notas ativas;
- ultima release;
- botao de inscricao/cancelamento;
- botao de compartilhar;
- link para pagina do baralho na Community;
- link para sugestoes da comunidade;
- lista de notas com preview e `public_id`;
- preview completo ao clicar em uma nota.

### Contratos Atuais

Ja existem:

```text
GET /addon/decks/{deck_id}/manifest
GET /addon/decks/{deck_id}/sync?since_release=0
```

Esses endpoints foram pensados para o add-on, mas conceitualmente entregam o
snapshot atual do deck para usuarios inscritos.

### Recomendacao Tecnica

Nao usar diretamente endpoints `/addon` no frontend web de estudante como
contrato final. Criar futuramente endpoints web equivalentes:

```text
GET /decks/public/{deck_id}
GET /decks/public/{deck_id}/notes
GET /decks/public/{deck_id}/notes/{card_id}
```

Motivo:

- endpoints `/addon` devem permanecer otimizados para sincronizacao;
- frontend web pode precisar de dados adicionais de apresentacao;
- evita misturar contrato de sync com contrato de leitura social.

Para MVP, a interface pode reutilizar os dados disponiveis pelo backend atual,
mas o documento de produto deve tratar isso como ponte temporaria.

## Lista De Notas No Deck

### Exibicao

Cada item deve mostrar:

- `public_id`;
- tipo: basic ou cloze;
- preview curto da frente/texto;
- tags, quando disponiveis;
- indicador de versao/release;
- acao `Visualizar`.

### O Que Nao Mostrar

Nao expor inicialmente:

- filtros por disciplina;
- filtros por topico;
- detalhes internos de curadoria;
- botoes administrativos para estudantes.

Esses dados podem continuar no backend para organizacao interna, importacao e
curadoria, mas nao precisam ser centrais na experiencia do estudante.

## Pop-up Da Nota

### Objetivo

Permitir leitura completa da nota sem sair do contexto do baralho.

### Conteudo

Mostrar:

- todos os campos da nota;
- `public_id`;
- `card_id` em area tecnica discreta ou copiar ID;
- tipo da nota;
- tags;
- release/versao quando aplicavel;
- botao `Sugerir mudancas`;
- area futura para comentarios publicos colaborativos.

### Sugestao De Layout

```text
Cabecalho:
  public_id, tipo, acoes

Conteudo:
  Frente / Texto
  Verso / Extra
  Resposta
  Explicacao
  Tags

Rodape:
  Sugerir mudancas
  Abrir na Community
  Compartilhar
```

## Sugerir Mudancas

### Objetivo

Transformar feedback do estudante em fluxo de curadoria sem permitir edicao
direta da nota publicada.

### Comportamento

Ao clicar em `Sugerir mudancas`, liberar um editor para sugestao. A interface
pode parecer um editor campo a campo, mas tecnicamente deve enviar uma proposta,
nao alterar a nota.

Regra obrigatoria:

```text
Sugestoes nunca editam card_versions publicadas.
Sugestoes devem virar report, comentario de curadoria ou futura review task.
```

### Tipo De Mudanca

Dropdown sugerida:

```text
Novo conteudo
Ortografia/Gramatica
Erro de conteudo
Novo cartao para adicionar
Novas tags
Tags atualizadas
Excluir nota
Outro
```

### Mapeamento Inicial Com Reports Atuais

O backend atual possui reports com tipos mais formais. A UI pode mapear:

| UI | Report atual sugerido |
|---|---|
| Ortografia/Gramatica | `typo` |
| Erro de conteudo | `wrong_answer` ou `bad_explanation` |
| Novo conteudo | `suggestion` |
| Novo cartao para adicionar | `suggestion` |
| Novas tags | `classification_error` ou `suggestion` |
| Tags atualizadas | `classification_error` |
| Excluir nota | `suggestion` ou futuro `remove_card` |
| Outro | `suggestion` |

### Dependencia Futura

Para uma experiencia rica com editor markdown por campo, o backend precisara
armazenar sugestoes estruturadas. Modelo conceitual futuro:

```text
card_suggestions
- id
- card_id
- card_version_id
- user_id
- change_type
- proposed_fields_json
- message
- status
- created_at
- updated_at
```

No MVP, usar reports existentes e salvar a proposta em texto estruturado.

## Editor Markdown Campo A Campo

### Recomendacao

O editor pode ser exibido no frontend como markdown, mas o conteudo enviado ao
backend deve ser tratado como sugestao textual ate existir um contrato
estruturado.

Evitar no MVP:

- aplicar diff automatico;
- permitir publicacao direta;
- comparar campos complexos sem revisao humana;
- aceitar HTML bruto sem sanitizacao.

### Barra De Formatacao

Controles recomendados:

- negrito;
- italico;
- codigo;
- lista;
- link;
- citacao;
- desfazer/refazer local;
- preview.

## Comentarios Publicos Colaborativos

### Objetivo Futuro

Criar uma camada social parecida com plataformas como Qconcursos e TEC
Concursos, permitindo que estudantes comentem:

- duvidas;
- dicas;
- mnemônicos;
- observacoes;
- explicacoes alternativas;
- possiveis erros.

### Regras De Produto

Comentarios nao devem alterar o conteudo oficial.

Separacao recomendada:

```text
Comentario publico -> camada social
Sugestao de mudanca -> fluxo de curadoria
Versao publicada -> conteudo oficial
```

### Modelo Futuro Conceitual

```text
card_comments
- id
- card_id
- card_version_id
- user_id
- parent_id
- body
- kind
- status
- score
- created_at
- updated_at
```

Kinds:

```text
comment
tip
mnemonic
question
correction
```

Status:

```text
visible
hidden
flagged
resolved
```

### Integracao Futura Com Add-on

Objetivo futuro:

```text
No Anki, o usuario clica em "Comentarios"
-> abre a pagina web da nota na plataforma/community
-> usuario ve comentarios, dicas e sugestoes
```

O add-on nao precisa renderizar comentarios dentro do Anki no MVP. Ele pode
apenas abrir a URL canonica da nota.

## Tela Dashboard Administrativo

### Objetivo

Concentrar operacoes editoriais e administrativas. Esta tela nao deve ser a
home do estudante.

### Conteudo Recomendado

Mostrar:

- baralhos em rascunho;
- baralhos publicados;
- baralhos com mudancas pendentes de release;
- sugestoes/reports pendentes;
- versoes pendentes de revisao;
- atalhos para publicar release;
- atalhos para revisar sugestoes;
- usuarios recentes ou pendencias de conta, apenas para admin.

### Contratos Atuais

Parte ja existe:

```text
GET /decks
GET /cards?status=needs_review
GET /admin/reports
GET /admin/users
POST /decks/{deck_id}/publish-release
```

### Lacunas

Ainda nao existe endpoint agregado de dashboard. Evitar calcular metricas
globais carregando listas inteiras no navegador.

Recomendacao futura:

```text
GET /admin/dashboard
```

Com resposta agregada:

```json
{
  "decks_with_unpublished_changes": 3,
  "pending_reports": 12,
  "versions_needing_review": 25,
  "latest_releases": []
}
```

## Tela Community

### Objetivo Futuro

Criar uma area publica/comunitaria em subdominio separado, por exemplo:

```text
community.ankiconcursos.com.br
```

### Escopo Futuro

A Community pode conter:

- pagina publica do baralho;
- comentarios do baralho;
- comentarios por nota;
- sugestoes de edicao;
- ranking de dicas uteis;
- discussoes moderadas;
- links compartilhaveis.

### Recomendacao

Nao implementar a Community completa agora. Preparar links e estrutura de URL
sem prometer funcionalidade ativa.

Exemplos de URLs futuras:

```text
/decks/{deck_id}
/decks/{deck_id}/suggestions
/notes/{public_id}
/notes/{public_id}/comments
```

## Remover Da Interface, Nao Do Backend

As seguintes areas devem ser removidas ou escondidas da interface principal do
estudante:

- Importacao CSV;
- sessao de cards filtrada por disciplina/topico/assunto;
- rota ativa `cards/new`;
- criacao manual de novo cartao fora do painel administrativo.

Importante:

```text
Nao remover endpoints nem tabelas do backend neste momento.
```

Motivos:

- importacao CSV ainda e util para administradores;
- disciplina/topico ainda podem apoiar organizacao interna;
- criacao manual de cartao ainda pode ser necessaria para curadoria;
- remocao de backend aumentaria risco sem ganho imediato.

### Onde Essas Funcoes Devem Ficar

Mover para area administrativa, se ainda forem necessarias:

```text
Administracao / Importacao
Administracao / Cartoes
Administracao / Taxonomia interna
```

Ou ocultar temporariamente por feature flag.

## Impacto No Projeto Atual

### Baixo Risco

- reorganizar menu;
- criar tela Explore;
- criar tela Deck focada em estudantes;
- esconder importacao CSV do fluxo principal;
- esconder `cards/new` para estudantes;
- criar links futuros para Community;
- criar pop-up de preview de nota;
- reaproveitar subscriptions e addon sync para leitura inicial.

### Medio Risco

- criar sugestoes estruturadas campo a campo;
- editor markdown com preview;
- comentarios publicos;
- busca real de decks no backend;
- dashboard administrativo agregado;
- URLs publicas canonicas por nota.

### Alto Risco

- remover disciplina/topico do banco;
- remover importacao CSV do backend;
- misturar comentarios publicos com reports formais;
- permitir edicao direta de conteudo publicado;
- transformar endpoints do add-on em API publica principal sem separar
  contratos.

## Ordem Recomendada De Implementacao

### Fase 1: Simplificacao Visual Sem Banco Novo

```text
1. Ajustar navegacao por papel
2. Criar Explore usando subscriptions
3. Criar tela Deck com dados basicos e lista de notas
4. Criar pop-up de preview da nota
5. Esconder CSV/cards/new do fluxo principal
6. Manter funcoes editoriais em Administracao
```

### Fase 2: Sugestoes De Mudanca

```text
1. Botao Sugerir mudancas
2. Dropdown de tipo de mudanca
3. Editor markdown simples
4. Envio como report/suggestion
5. Admin revisa no fluxo existente
```

### Fase 3: Community Preparada

```text
1. Definir URLs publicas de baralho e nota
2. Adicionar links placeholder seguros
3. Criar documentacao de comentarios publicos
4. Planejar card_comments
```

### Fase 4: Comentarios Publicos

```text
1. Criar tabela card_comments
2. Criar endpoints de comentarios
3. Criar moderacao basica
4. Integrar nota web com comentarios
5. Add-on abre link da nota/comentarios
```

## Regras Que Nao Devem Ser Quebradas

1. `card_id` continua sendo a identidade estavel.
2. `card_version_id` continua representando conteudo especifico.
3. Versao publicada nunca e editada diretamente.
4. Sugestoes criam fluxo de revisao, nao alteracao direta.
5. Releases continuam imutaveis.
6. Add-on continua sincronizando por deck/release/card_id.
7. Estudante nao acessa endpoints administrativos.
8. Comentarios publicos nao substituem reports formais.
9. Funcoes removidas da interface nao devem ser removidas do backend sem novo
   planejamento.

## Decisao Recomendada

Adotar a mudanca de fluxo de forma progressiva.

O produto deve se apresentar para estudantes como uma plataforma de decks
assinaveis com notas, comentarios e sugestoes. A complexidade de cartoes,
disciplinas, versoes, releases e importacao deve ficar no painel administrativo.

Resumo:

```text
Estudante ve: Explore, Deck, Nota, Comentarios, Sugestoes.
Admin ve: Curadoria, Cartoes, Importacao, Releases, Usuarios.
Backend mantem: versionamento, taxonomia, imports, reports e sync.
```
