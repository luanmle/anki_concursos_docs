# Especificação da Interface Administrativa e Frontend

## 1. Objetivo

Este documento orienta:

- a criação do design da interface no Google Stitch;
- a implementação do frontend administrativo;
- a integração exclusiva com a API FastAPI existente;
- a validação funcional, visual, responsiva e de acessibilidade.

A interface administra flashcards versionados para concursos públicos. Ela deve
permitir cadastrar, revisar, publicar, organizar e distribuir cartões sem
violar as regras de versionamento do backend.

O frontend não acessa o PostgreSQL diretamente e não recria regras de negócio.
Toda alteração persistente deve ocorrer por um endpoint da API.

## 2. Contexto do produto

O sistema mantém:

- identidade estável do cartão por `card_id` e `public_id`;
- conteúdo imutável por `card_version_id`;
- histórico completo de versões;
- taxonomia controlada por disciplina e assunto;
- revisão e publicação em etapas;
- decks compostos apenas por versões publicadas;
- releases imutáveis com deltas;
- reports de usuários e decisões auditáveis;
- usuários administrativos com papéis distintos.

Regra central:

```text
Nunca editar uma versão publicada.
Toda mudança pedagógica cria uma nova versão.
```

Fluxo principal:

```text
Cadastrar cartão
→ revisar
→ aprovar
→ publicar
→ adicionar ao deck
→ publicar release
→ exportar CSV
```

Fluxo de correção:

```text
Abrir cartão publicado
→ criar nova versão com change_reason
→ revisar
→ aprovar
→ publicar
→ atualizar explicitamente o cartão no deck
→ publicar nova release
```

## 3. Público da interface

A interface é interna e destinada a:

- `admin`: administração completa, inclusive usuários;
- `curator`: cadastro de cartões, novas versões e composição de decks;
- `reviewer`: aprovação, publicação, releases e revisão de reports.

Todos os papéis podem consultar cartões, taxonomia, decks, releases e sync.

## 4. Matriz de permissões

| Recurso | Admin | Curator | Reviewer |
|---|---:|---:|---:|
| Consultar cartões e versões | Sim | Sim | Sim |
| Criar cartão | Sim | Sim | Não |
| Criar nova versão | Sim | Sim | Não |
| Aprovar versão | Sim | Não | Sim |
| Publicar versão | Sim | Não | Sim |
| Consultar taxonomia | Sim | Sim | Sim |
| Criar deck | Sim | Sim | Não |
| Adicionar ou remover cartão do deck | Sim | Sim | Não |
| Publicar release | Sim | Não | Sim |
| Consultar releases, sync e exportar CSV | Sim | Sim | Sim |
| Consultar e revisar reports | Sim | Não | Sim |
| Criar e administrar usuários | Sim | Não | Não |

A interface deve esconder ações sem permissão. O backend continua sendo a fonte
de verdade e pode responder `403`; nesse caso, exibir mensagem clara e não
repetir automaticamente a operação.

## 5. Direção visual para o Google Stitch

### 5.1 Personalidade

A interface deve transmitir:

- precisão;
- confiança;
- organização;
- auditabilidade;
- foco em leitura prolongada;
- sobriedade compatível com conteúdo jurídico e educacional.

Evitar aparência de rede social, gamificação, excesso de gradientes, glassmorphism
intenso ou painéis com muitos cards decorativos.

### 5.2 Estilo recomendado

- dashboard administrativo desktop-first e responsivo;
- navegação lateral fixa em telas largas;
- cabeçalho superior compacto com ambiente, usuário e logout;
- superfícies claras, bordas discretas e hierarquia tipográfica forte;
- cor primária azul-marinho ou azul institucional;
- cor de destaque azul médio;
- verde apenas para sucesso/publicado;
- âmbar para revisão/atenção;
- vermelho para erro, remoção e depreciação;
- cinza para estados arquivados, rejeitados ou superseded.

### 5.3 Tokens visuais sugeridos

```text
Fonte: Inter, Source Sans 3 ou equivalente sem serifa
Raio pequeno: 6 px
Raio padrão: 10 px
Espaçamento base: 4 px
Altura de campos: 40 a 44 px
Largura máxima de conteúdo textual: 900 a 1100 px
Sidebar desktop: 240 a 272 px
Breakpoint mobile principal: 768 px
```

Paleta conceitual:

```text
primary-900: azul-marinho para navegação e títulos
primary-600: ações principais e links
neutral-950: texto principal
neutral-600: texto secundário
neutral-200: bordas
neutral-50: fundos
success-600: publicado, concluído, ativo
warning-600: needs_review, reported, pendente
danger-600: erro, removed, deprecated, inativo
```

O código final deve centralizar cores, tipografia, espaçamentos, sombras e
breakpoints como design tokens. Não espalhar valores visuais arbitrários.

### 5.4 Acessibilidade

- contraste mínimo WCAG AA;
- foco de teclado sempre visível;
- navegação completa por teclado;
- labels persistentes em todos os campos;
- não usar somente cor para comunicar status;
- ícones acompanhados de texto ou `aria-label`;
- mensagens de erro associadas ao campo;
- modais com foco preso e retorno de foco ao elemento de origem;
- tabelas com cabeçalhos semânticos;
- botões com estado de carregamento anunciado;
- respeitar `prefers-reduced-motion`;
- alvos de toque com pelo menos 44 x 44 px em mobile.

## 6. Estrutura de navegação

### 6.1 Menu principal

```text
Visão geral
Cartões
Decks
Reports
Usuários          somente admin
Operação
```

Taxonomia é usada como filtro e seleção dentro de cartões e decks. Como a API
atual permite apenas consulta, não deve existir ação de criar, editar ou excluir
disciplinas e assuntos.

### 6.2 Cabeçalho

Exibir:

- nome curto do produto;
- indicador de ambiente, como `STAGING` ou `PRODUCTION`;
- status de conectividade quando necessário;
- nome e papel do usuário;
- menu de conta;
- ação `Sair`.

Em produção, o indicador de ambiente deve ser discreto. Em staging, deve ser
visível para reduzir alterações no ambiente errado.

### 6.3 Breadcrumbs

Usar em páginas profundas:

```text
Cartões / AC-... / Versão 3
Decks / Direito Constitucional / Release 12
Reports / Report ...
Usuários / Editar usuário
```

## 7. Rotas do frontend

Sugestão de rotas:

```text
/login
/
/cards
/cards/new
/cards/:cardId
/cards/:cardId/versions/new
/decks
/decks/new
/decks/:deckId
/decks/:deckId/releases
/reports
/reports/:reportId
/users
/users/new
/users/:userId
/operation
/forbidden
```

Rotas privadas exigem sessão válida. A rota de usuários exige papel `admin`.
As ações internas de cada página também respeitam a matriz de permissões.

## 8. Telas e requisitos

### 8.1 Login

Elementos:

- marca/nome do produto;
- campo de e-mail;
- campo de senha;
- botão `Entrar`;
- estado de carregamento;
- erro genérico para credenciais inválidas;
- aviso de ambiente quando não for produção.

Regras:

- enviar `POST /auth/token`;
- não revelar se um e-mail existe;
- após sucesso, carregar a identidade retornada e validar com `GET /auth/me`;
- redirecionar para a rota originalmente solicitada;
- não incluir cadastro público, recuperação automática ou login social, pois
  esses contratos não existem na API atual.

### 8.2 Visão geral

Objetivo: orientar o trabalho, não criar métricas falsas.

A API atual não possui endpoint agregado de dashboard. A primeira versão pode
mostrar:

- atalhos de acordo com o papel;
- links para cartões, decks, reports e usuários;
- status de `/health` e `/ready`;
- identificação do ambiente e da API;
- instrução breve do fluxo editorial.

Não exibir contadores globais, gráficos ou tendências sem endpoint específico.
Não carregar todas as páginas de listagem para calcular métricas no navegador.

### 8.3 Lista de cartões

Endpoint:

```text
GET /cards
```

Filtros suportados:

- disciplina;
- assunto;
- status;
- `public_id`;
- página;
- itens por página.

Colunas recomendadas:

- `public_id`;
- chave canônica;
- disciplina;
- assunto;
- status do cartão;
- versão atual e status da versão;
- data de atualização;
- ações.

Ações:

- abrir detalhes;
- criar cartão, para `admin` e `curator`.

Comportamento:

- filtros refletidos na URL;
- debounce somente na busca textual por `public_id`;
- paginação server-side;
- opção de 20, 50 ou 100 itens;
- estado vazio com ação contextual;
- status apresentados como badges com texto traduzido.

### 8.4 Cadastro de cartão

Endpoint:

```text
POST /cards
```

Campos:

- chave canônica;
- disciplina;
- assunto dependente da disciplina;
- frente;
- verso;
- resposta;
- explicação;
- motivo da criação, preenchido por padrão como `Versao inicial`.

Não solicitar `created_by`; a API substitui esse valor pelo e-mail autenticado.

UX:

- formulário em seções;
- contador de caracteres;
- preview lado a lado ou alternável;
- aviso de que o cartão será criado em `needs_review`;
- confirmar saída quando houver alterações não salvas;
- foco no primeiro campo inválido;
- desabilitar o envio durante a requisição.

### 8.5 Detalhe do cartão

Endpoint:

```text
GET /cards/{card_id}
```

Cabeçalho:

- `public_id` com ação de copiar;
- chave canônica;
- disciplina e assunto;
- status;
- versão atual;
- datas.

Conteúdo:

- abas `Conteúdo atual`, `Histórico` e `Metadados`;
- frente, verso, resposta e explicação com boa legibilidade;
- lista cronológica de versões;
- status, autor, motivo, hash e data de cada versão;
- comparação visual entre duas versões quando implementada no cliente.

Ações condicionais:

- `Nova versão`: admin e curator;
- `Aprovar`: admin e reviewer, somente para versão em `needs_review`;
- `Publicar`: admin e reviewer, somente para versão `approved`;
- copiar IDs;
- abrir consulta pública quando o cartão estiver publicado.

Não oferecer:

- editar versão existente;
- excluir versão;
- alterar status diretamente;
- publicar versão ainda não aprovada.

### 8.6 Nova versão

Endpoint:

```text
POST /cards/{card_id}/versions
```

Campos:

- frente;
- verso;
- resposta;
- explicação;
- `change_reason` obrigatório.

Preencher o formulário com o conteúdo da versão escolhida, mas salvar como nova
versão. Exibir claramente:

```text
Você está criando uma nova versão. A versão publicada permanecerá preservada.
```

A API atual não aceita disciplina ou assunto nessa operação. Portanto, o
frontend não deve permitir reclassificação nesta tela até que o backend ofereça
um contrato específico.

### 8.7 Aprovação e publicação

Endpoints:

```text
POST /cards/{card_id}/versions/{version_id}/approve
POST /cards/{card_id}/versions/{version_id}/publish
```

Antes de aprovar:

- mostrar conteúdo completo;
- mostrar `change_reason`;
- confirmar que a versão foi revisada.

Antes de publicar:

- mostrar versão e cartão;
- destacar que a versão se tornará pública;
- lembrar que decks não são atualizados automaticamente.

Após sucesso:

- atualizar cache do cartão e listas;
- mostrar feedback persistente;
- oferecer link para adicionar/atualizar o cartão em um deck.

### 8.8 Lista de decks

Endpoint:

```text
GET /decks
```

Colunas:

- nome;
- disciplina;
- status;
- quantidade de cartões ativos;
- atualização;
- ações.

Ações:

- abrir deck;
- criar deck, para admin e curator.

Não exibir edição, arquivamento ou exclusão, pois não existem endpoints atuais
para essas operações.

### 8.9 Criação de deck

Endpoint:

```text
POST /decks
```

Campos:

- nome;
- disciplina opcional;
- descrição opcional.

Informar que o deck nasce como rascunho e só recebe uma release após possuir
mudanças publicáveis.

### 8.10 Detalhe do deck

Endpoint:

```text
GET /decks/{deck_id}
```

Exibir:

- nome, descrição, disciplina e status;
- cartões ativos;
- `public_id`, versão, data de inclusão;
- link para o cartão;
- aba de releases.

Ações para admin e curator:

- adicionar cartão publicado;
- remover cartão com ação `removed`;
- depreciar cartão com ação `deprecated`.

Endpoints:

```text
POST /decks/{deck_id}/cards
POST /decks/{deck_id}/cards/{card_id}/remove
```

Ao adicionar:

- permitir busca de cartão;
- indicar que apenas a versão atual publicada pode entrar no deck;
- prevenir seleção duplicada no cliente e tratar conflito do servidor.

Ao remover:

- exigir confirmação;
- explicar a diferença entre `removed` e `deprecated`;
- usar linguagem de alto impacto para `deprecated`.

### 8.11 Releases

Endpoints:

```text
GET /decks/{deck_id}/releases
POST /decks/{deck_id}/publish-release
GET /decks/{deck_id}/sync?since_release={n}
GET /decks/{deck_id}/releases/{release_id}/export.csv
```

Lista:

- número da release;
- data;
- descrição;
- total de itens;
- contagens de `added`, `updated`, `removed` e `deprecated`;
- ação de exportar.

Publicação:

- disponível para admin e reviewer;
- solicitar descrição opcional;
- mostrar aviso de imutabilidade;
- tratar ausência de mudanças como erro esperado e explicável.

Exportação:

- seletor de delimitador: vírgula, ponto e vírgula ou tabulação;
- opção de incluir tags;
- download iniciado pelo backend;
- mostrar número da release, quantidade de linhas e hash SHA-256 quando os
  headers estiverem disponíveis.

Visualização de sync:

- informar release inicial e final;
- timeline em ordem crescente;
- badges para cada ação;
- exibir IDs de versão anterior e nova;
- não apresentar o sync como editor.

A API atual não possui endpoint de detalhe completo de uma release. A interface
deve usar os dados da listagem e do sync, sem inventar uma tela de itens que
dependa de dados indisponíveis.

### 8.12 Lista de reports

Endpoint:

```text
GET /admin/reports
```

Filtros:

- status;
- tipo;
- página;
- itens por página.

Colunas:

- `public_id`;
- versão reportada;
- tipo;
- status;
- status da tarefa;
- referência do reportante;
- data;
- ação `Revisar`.

Tipos:

```text
typo
wrong_answer
outdated_law
bad_explanation
classification_error
duplicate_card
suggestion
```

### 8.13 Revisão de report

Endpoint:

```text
GET /admin/reports/{report_id}
POST /admin/reports/{report_id}/review
```

Layout recomendado:

- coluna esquerda: report, mensagem, metadados e versão reportada;
- coluna direita: decisão e comentário administrativo;
- acesso direto ao detalhe completo do cartão;
- em telas pequenas, empilhar as seções.

Decisões atuais:

```text
rejected
duplicate
converted_to_new_version
```

Regras:

- `admin_comment` sempre obrigatório;
- `outdated_law` exige `evidence_reviewed=true`;
- conversão exige frente, verso, resposta, explicação e `change_reason`;
- rejeição e duplicidade não alteram o cartão;
- conversão cria nova versão em `needs_review`;
- versão publicada reportada permanece atual.

Após conversão, oferecer link para a nova versão e indicar que ela ainda precisa
ser aprovada e publicada.

Não mostrar decisões conceituais que não existem no enum atual, como `approved`
ou `needs_more_info`.

### 8.14 Usuários

Endpoints:

```text
GET /admin/users
POST /admin/users
PATCH /admin/users/{user_id}
POST /admin/users/{user_id}/reset-password
```

Lista:

- nome;
- e-mail;
- papel;
- ativo/inativo;
- último login;
- criação;
- ações.

Criação:

- nome;
- e-mail;
- papel;
- senha inicial.

Edição:

- nome;
- papel;
- ativo/inativo.

Redefinição de senha:

- modal separado;
- mínimo de 12 caracteres;
- confirmação da nova senha no cliente;
- após sucesso, informar que tokens anteriores foram revogados.

Restrições:

- somente admin;
- não implementar exclusão;
- confirmar desativação;
- tratar tentativa inválida de autodesativação ou alteração crítica conforme a
  resposta do backend.

### 8.15 Operação

Endpoints:

```text
GET /health
GET /ready
GET /
```

Exibir:

- serviço acessível;
- banco disponível;
- URL base da API;
- ambiente;
- horário da última verificação;
- botão de atualizar.

Não exibir logs, secrets, `DATABASE_URL`, tokens ou Config Vars.

## 9. Tradução de estados

Manter o valor técnico disponível em tooltip ou detalhe, mas usar rótulos em
português:

```text
needs_review  → Precisa de revisão
approved      → Aprovado
published     → Publicado
reported      → Reportado
revised       → Revisado
deprecated    → Depreciado
archived      → Arquivado
rejected      → Rejeitado
superseded    → Substituído
draft         → Rascunho
open          → Aberto
in_review     → Em revisão
resolved      → Resolvido
pending       → Pendente
assigned      → Atribuído
completed     → Concluído
cancelled     → Cancelado
added         → Adicionado
updated       → Atualizado
removed       → Removido
duplicate     → Duplicado
converted_to_new_version → Convertido em nova versão
```

Centralizar esse mapeamento. Não repetir traduções em componentes diferentes.

## 10. Contrato de autenticação

Login:

```http
POST /auth/token
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "senha"
}
```

Resposta:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "...",
    "email": "admin@example.com",
    "display_name": "Administrador",
    "role": "admin",
    "is_active": true
  }
}
```

Requisições privadas:

```http
Authorization: Bearer <access_token>
```

Validação da sessão:

```text
GET /auth/me
```

Regras do cliente:

- manter o token fora de logs, URLs, analytics e mensagens de erro;
- preferir armazenamento em memória com persistência opcional em
  `sessionStorage`;
- não usar `localStorage` como padrão para sessão administrativa persistente;
- limpar token e dados do usuário ao sair;
- em `401`, limpar a sessão e redirecionar para login;
- em `403`, manter a sessão e mostrar acesso negado;
- não existe refresh token ou endpoint de logout no backend atual;
- logout é local;
- alteração de senha revoga tokens anteriores.

## 11. Integração HTTP

Configuração por ambiente:

```text
VITE_API_URL=https://flashcards-stagging-d9c092f5d04d.herokuapp.com
```

Nunca fixar a URL da API diretamente nos componentes.

O cliente HTTP deve:

- adicionar `Authorization` quando houver sessão;
- enviar e aceitar JSON;
- preservar downloads CSV como `Blob`;
- capturar `X-Request-ID` para suporte;
- tratar `Content-Disposition`;
- ler `X-Content-SHA256`, `X-Row-Count` e `X-Release-Number`;
- cancelar requisições obsoletas em filtros e navegação;
- diferenciar erro de validação, autenticação, autorização, conflito,
  indisponibilidade e falha de rede.

Formato comum de erro FastAPI:

```json
{
  "detail": "Mensagem"
}
```

Erros de validação podem retornar `detail` como lista. Criar um normalizador
único de erros para mensagens de página, toast e campos.

## 12. Arquitetura frontend recomendada

Stack sugerida:

```text
React
TypeScript com strict=true
Vite
React Router
TanStack Query
React Hook Form
Zod
Vitest
Testing Library
Playwright
```

Uma biblioteca de componentes acessíveis pode ser usada, desde que os tokens
visuais e o comportamento permaneçam sob controle do projeto.

Estrutura sugerida:

```text
admin/
  src/
    app/
    routes/
    features/
      auth/
      cards/
      decks/
      reports/
      users/
      operation/
    components/
    design-system/
    api/
    hooks/
    lib/
    types/
    test/
  public/
```

Princípios:

- organizar por feature;
- separar componentes visuais de integração HTTP;
- usar tipos explícitos para requests e responses;
- centralizar query keys;
- invalidar somente caches afetados;
- não guardar respostas remotas duplicadas em estado global;
- não duplicar regras de permissão em vários componentes;
- criar um único `PermissionGate`;
- manter formulários e mutações próximos da feature.

## 13. Cache e atualização

Sugestão de query keys:

```text
["me"]
["disciplines"]
["topics", disciplineId]
["cards", filters]
["card", cardId]
["decks", pagination]
["deck", deckId]
["releases", deckId, pagination]
["sync", deckId, sinceRelease]
["reports", filters]
["report", reportId]
["users", pagination]
["operation"]
```

Após mutações:

- criar cartão: invalidar lista de cartões;
- criar/aprovar/publicar versão: invalidar cartão e listas;
- criar deck: invalidar lista de decks;
- adicionar/remover cartão: invalidar deck;
- publicar release: invalidar deck, releases e sync;
- revisar report: invalidar report, lista de reports e cartão relacionado;
- alterar usuário: invalidar usuário/lista e `me` quando for o usuário atual.

Não usar atualizações otimistas em aprovação, publicação, release, revisão de
report ou redefinição de senha. Essas operações possuem regras críticas e devem
aguardar confirmação do servidor.

## 14. Componentes compartilhados

Componentes mínimos:

- `AppShell`;
- `Sidebar`;
- `Topbar`;
- `EnvironmentBadge`;
- `Breadcrumbs`;
- `PageHeader`;
- `DataTable`;
- `Pagination`;
- `FilterBar`;
- `StatusBadge`;
- `EmptyState`;
- `ErrorState`;
- `LoadingSkeleton`;
- `ConfirmDialog`;
- `PermissionGate`;
- `CopyButton`;
- `DateTime`;
- `IdDisplay`;
- `FormField`;
- `TextareaWithCounter`;
- `UnsavedChangesGuard`;
- `VersionTimeline`;
- `CardContentPreview`;
- `ReleaseActionSummary`;
- `RequestErrorAlert`.

Não criar componentes genéricos excessivamente abstratos antes de existirem
dois ou mais usos concretos.

## 15. Estados obrigatórios de UX

Toda tela de dados deve projetar:

- carregamento inicial;
- atualização em segundo plano;
- sucesso;
- lista vazia;
- filtro sem resultado;
- erro recuperável;
- erro de autenticação;
- acesso negado;
- recurso não encontrado;
- indisponibilidade da API;
- indisponibilidade do banco;
- ação em progresso;
- confirmação de ação crítica.

Nunca deixar uma tabela vazia sem explicar o motivo.

## 16. Responsividade

Desktop:

- sidebar fixa;
- tabelas completas;
- formulários em até duas colunas quando adequado;
- detalhe de report em duas colunas.

Tablet:

- sidebar recolhível;
- filtros em painel;
- tabelas com colunas secundárias ocultáveis.

Mobile:

- navegação em drawer;
- tabelas transformadas em listas/cards sem perder ações;
- ações críticas em menu contextual;
- formulários em uma coluna;
- botões principais ocupando largura adequada;
- preservar acesso a IDs, status e histórico.

A interface é desktop-first, mas nenhuma operação essencial pode depender de
hover ou ficar inacessível em telas menores.

## 17. Segurança do frontend

- não armazenar senha;
- não registrar token;
- não inserir HTML de conteúdo sem sanitização;
- renderizar textos dos cartões como texto por padrão;
- não confiar no papel salvo no cliente sem validar `/auth/me`;
- não expor secrets em variáveis `VITE_*`;
- não colocar credenciais em arquivos versionados;
- configurar `CORS_ORIGINS` no backend com a origem exata do frontend;
- não usar `*` para CORS administrativo;
- proteger contra envio duplo;
- invalidar sessão após `401`;
- exibir `X-Request-ID` em detalhes de erro para suporte;
- evitar mensagens que revelem existência de usuários no login.

## 18. Limitações atuais da API

O design não deve inventar funcionalidades sem contrato:

- não existe refresh token;
- não existe logout no servidor;
- não existe recuperação de senha por e-mail;
- não existe endpoint agregado de dashboard;
- não existe criação/edição de disciplina ou assunto;
- não existe edição, arquivamento ou exclusão de deck;
- não existe exclusão de cartão ou versão;
- não existe edição direta de versão;
- não existe alteração de disciplina/assunto na criação de nova versão;
- não existe endpoint de detalhe completo de release;
- não existe endpoint de quality checks detalhados;
- não existe upload ou processamento de documentos;
- não existe geração de cartões por IA;
- não existe sincronização direta com o Anki.

Essas ações podem aparecer em um roadmap, mas não em botões ativos, menus ou
protótipos que pareçam funcionais.

## 19. Testes do frontend

### 19.1 Unitários

- tradução de status;
- normalização de erros;
- regras de permissão;
- formatação de datas e IDs;
- construção de parâmetros de busca;
- tratamento de headers de exportação.

### 19.2 Componentes

- login válido e inválido;
- campos e validações;
- tabelas, paginação e filtros;
- estados vazios e de erro;
- diálogos de confirmação;
- ações ocultas por papel;
- formulários de cartão, versão, deck, report e usuário.

### 19.3 Integração

- sessão validada com `/auth/me`;
- `401` encerra sessão;
- `403` mostra acesso negado;
- criar cartão e abrir detalhe;
- criar, aprovar e publicar versão;
- adicionar cartão ao deck;
- publicar release;
- baixar CSV;
- revisar report;
- administrar usuário.

### 19.4 E2E

Fluxos críticos:

```text
admin faz login
→ cria cartão
→ aprova
→ publica
→ cria deck
→ adiciona cartão
→ publica release
→ exporta CSV
```

```text
reporter gera report
→ reviewer abre report
→ converte em nova versão
→ aprova
→ publica
```

Testar separadamente permissões de `admin`, `curator` e `reviewer`.

## 20. Critérios de aceite

A primeira versão está pronta quando:

- login e logout local funcionam;
- sessão expirada é tratada;
- navegação muda conforme o papel;
- cartões podem ser listados, filtrados, criados e consultados;
- histórico de versões é legível;
- nova versão nunca sobrescreve uma versão anterior;
- reviewer consegue aprovar e publicar;
- decks podem ser criados e compostos;
- releases podem ser publicadas e exportadas;
- reports podem ser filtrados e revisados;
- admin consegue administrar usuários;
- `/health` e `/ready` podem ser consultados;
- erros mostram mensagem útil e `X-Request-ID` quando disponível;
- layout funciona em desktop, tablet e mobile;
- navegação por teclado e contraste atendem WCAG AA;
- não há ação visual sem endpoint correspondente;
- testes críticos passam em CI.

## 21. Entregáveis do Google Stitch

Solicitar ao Stitch:

1. mapa completo de telas;
2. layout desktop de todas as telas principais;
3. versões mobile de login, lista de cartões, detalhe de cartão, deck e report;
4. design system com cores, tipografia, espaçamento, botões, campos e badges;
5. estados de loading, vazio, erro, sucesso, `401`, `403` e `404`;
6. modais de aprovação, publicação, remoção, depreciação e redefinição de senha;
7. tabelas e filtros responsivos;
8. timeline de versões;
9. resumo de ações de release;
10. protótipo navegável do fluxo principal.

Os arquivos exportados pelo Stitch são referência visual. Antes de integrar,
revisar semântica HTML, acessibilidade, responsividade, tokens, dependências e
aderência aos contratos reais da API.

## 22. Prompt-base para o Google Stitch

```text
Crie uma interface administrativa responsiva para "Anki Concursos", uma
plataforma brasileira de gestão de flashcards versionados para concursos
públicos.

O produto é interno, orientado a precisão, revisão humana, auditabilidade e
conteúdo jurídico/educacional. Use visual sóbrio, profissional e claro, com
sidebar desktop, topbar compacta, tipografia sem serifa, azul institucional,
fundos neutros, bordas discretas e badges de status acessíveis. Evite
gamificação, excesso de cards decorativos, gradientes intensos e glassmorphism.

Papéis: admin, curator e reviewer. Admin gerencia tudo e usuários. Curator cria
cartões, novas versões e compõe decks. Reviewer aprova e publica versões,
publica releases e revisa reports.

Telas: login; visão geral sem métricas inventadas; lista e cadastro de cartões;
detalhe do cartão com conteúdo atual e timeline imutável de versões; criação de
nova versão; lista, criação e detalhe de decks; composição de deck; lista e
publicação de releases; exportação CSV; lista e revisão de reports; lista,
criação e edição de usuários; status operacional.

Regra visual e funcional central: versões publicadas nunca são editadas. Uma
mudança cria nova versão, passa por aprovação e publicação. Decks e releases não
são atualizados automaticamente.

Projete loading, vazio, filtro sem resultado, erro, sucesso, acesso negado,
sessão expirada e confirmações críticas. Crie versões desktop e mobile. Atenda
WCAG AA, navegação por teclado, foco visível e não use somente cor para status.

Não desenhe funções inexistentes: editar versão publicada, excluir cartão,
editar/excluir deck, editar taxonomia, recuperar senha por e-mail, refresh token,
dashboard com gráficos, upload de documentos ou geração por IA.
```

## 23. Sequência recomendada de implementação

```text
1. Scaffold do frontend e design tokens
2. Cliente HTTP e configuração por ambiente
3. Login, sessão, guards e permissões
4. App shell e navegação
5. Taxonomia e componentes compartilhados
6. Cartões e versionamento
7. Aprovação e publicação
8. Decks
9. Releases, sync e CSV
10. Reports
11. Usuários
12. Operação
13. Responsividade e acessibilidade
14. Testes E2E
15. Deploy de staging e configuração de CORS
```

## 24. Deploy do frontend

O frontend pode permanecer no mesmo repositório, em `admin/`, mas deve possuir
deploy separado do backend.

Neste repositório, a imagem do frontend é definida por `admin/Dockerfile`. Ela
gera os arquivos estáticos com Node e os serve com Nginx. A aplicação recebe em
runtime:

```text
API_URL=https://api-do-ambiente.herokuapp.com
APP_ENV=STAGING|PRODUCTION
PORT=<fornecida pelo Heroku>
```

O frontend deve ser publicado em outro app Heroku, sem Heroku Postgres, sem
migrations e sem acesso a `DATABASE_URL`. O app de backend continua usando o
`Dockerfile`, `Procfile` e `heroku.yml` da raiz.

O deploy usa duas branches:

```text
main         -> backend
admin-deploy -> frontend
```

O workflow `.github/workflows/publish-admin-deploy.yml` valida o frontend e
gera `admin-deploy` por `git subtree split --prefix=admin`. Nessa branch,
`admin/Dockerfile` e `admin/heroku.yml` aparecem na raiz, como esperado pelo
Heroku.

`admin-deploy` não é uma branch de desenvolvimento. Não editar seus arquivos,
abrir PRs contra ela ou fazer merge dela para `main`. Toda mudança nasce em
`admin/` na branch principal.

Ambientes:

```text
admin staging   → API staging
admin production → API production
```

Após publicar o frontend:

1. configurar `VITE_API_URL`;
2. adicionar a origem exata em `CORS_ORIGINS` no backend;
3. validar login;
4. validar `/auth/me`;
5. executar os fluxos críticos;
6. confirmar que staging não aponta para a API de produção;
7. confirmar que nenhum secret foi incluído no bundle.
