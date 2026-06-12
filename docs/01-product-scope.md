# Escopo do Produto

## Visão geral

O projeto é um ecossistema automatizado de processamento de dados voltado para educação e concursos públicos.

Ele resolve a dor da fragmentação e desatualização de materiais de estudo, transformando provas brutas em flashcards atômicos, categorizados, fundamentados, revisados e versionados.

## O que o sistema faz

### 1. Ingestão e leitura de documentos

O sistema recebe cadernos de provas, extrai o texto bruto e identifica onde começa e termina cada questão.

### 2. Classificação inteligente

Cada questão é classificada automaticamente por:

- disciplina;
- assunto;
- subassunto;
- banca;
- concurso;
- cargo;
- ano.

A classificação automática deve ser revisável.

### 3. Transformação em flashcard

Questões longas de múltipla escolha são convertidas em cartões objetivos de pergunta e resposta.

O cartão deve ser atômico: uma pergunta principal, uma resposta clara e uma fundamentação.

### 4. Enriquecimento com base teórica

O sistema consulta uma base teórica própria, como leis, resumos, súmulas e comentários, para justificar a resposta.

A fundamentação precisa ser armazenada e vinculada ao cartão.

### 5. Versionamento seguro

Cada cartão possui identidade fixa.

Quando o conteúdo muda, o sistema não edita o cartão antigo diretamente. Ele cria uma nova versão.

### 6. Curadoria colaborativa

Usuários podem reportar erros, sugerir melhorias ou apontar desatualizações.

Administradores revisam essas sugestões e, quando aprovadas, geram uma nova versão do cartão.

### 7. Distribuição e sincronização

O sistema organiza os cartões em baralhos e publica releases.

No futuro, usuários poderão sincronizar apenas mudanças incrementais, sem perder histórico de revisão.
