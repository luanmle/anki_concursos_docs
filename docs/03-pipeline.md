# Pipeline de Processamento

## Objetivo

Transformar documentos brutos de provas em flashcards versionados, fundamentados e prontos para revisão/publicação.

## Pipeline principal

```text
1. Upload do documento
2. Extração de texto
3. Segmentação em questões
4. Extração de alternativas e gabarito
5. Classificação por disciplina e assunto
6. Geração de flashcard
7. Busca de fundamentação
8. Validação automática
9. Revisão administrativa
10. Publicação em baralho
11. Geração de release
```

## Etapas detalhadas

### 1. Upload do documento

Entrada:

- PDF da prova;
- metadados opcionais;
- banca;
- ano;
- cargo;
- órgão;
- tipo de prova.

Saída:

- registro em `raw_documents`;
- arquivo salvo em storage;
- hash do arquivo salvo.

### 2. Extração de texto

Ferramentas sugeridas:

- PyMuPDF;
- pdfplumber;
- Tesseract OCR para PDF escaneado.

Saída:

- `raw_text`;
- status de extração;
- logs em `processing_jobs`.

### 3. Segmentação de questões

O sistema deve identificar:

- número da questão;
- enunciado;
- alternativas;
- gabarito quando disponível.

Saída:

- registros em `questions`;
- registros em `question_alternatives`.

### 4. Classificação

A questão deve ser classificada por disciplina e assunto.

Classificações devem usar a taxonomia oficial.

Saída:

- registro em `question_classifications`;
- score de confiança.

### 5. Geração do flashcard

A questão é transformada em cartão atômico.

Regras:

- frente objetiva;
- verso autoexplicativo;
- resposta clara;
- não copiar desnecessariamente a questão inteira;
- preservar vínculo com a questão original;
- marcar como `generated` ou `needs_review`.

Saída:

- registro em `cards`;
- registro em `card_versions`.

### 6. Busca de fundamentação

O sistema deve buscar trechos na base teórica.

Usar busca híbrida:

- busca textual;
- busca semântica por embeddings;
- filtros por disciplina, assunto, vigência e fonte.

Saída:

- registros em `card_evidence`.

### 7. Validação automática

Executar checks:

- a questão tem enunciado?
- existe resposta?
- existe fundamentação?
- há duplicidade?
- disciplina está válida?
- assunto está válido?
- frente é atômica?
- verso possui explicação?
- evidência sustenta resposta?

Saída:

- registros em `quality_checks`.

### 8. Revisão administrativa

O admin pode:

- aprovar;
- reprovar;
- editar e gerar nova versão;
- solicitar reprocessamento;
- alterar classificação;
- alterar fundamentação.

### 9. Publicação

Após aprovação, o cartão pode entrar em um baralho.

Saída:

- `deck_cards`;
- status `published`.

### 10. Release

Mudanças são agrupadas em releases.

A release informa:

- cartões adicionados;
- cartões atualizados;
- cartões removidos;
- cartões depreciados.

Saída:

- `releases`;
- `release_items`.
