

Este projeto integra o Honeybadger apenas no backend FastAPI. A API key deve
ser fornecida exclusivamente pela variável de ambiente `HONEYBADGER_API_KEY`.

## Configuração

Defina a variável no ambiente local ou no Heroku:

```bash
HONEYBADGER_API_KEY=your-key-here
```

No Heroku, configure a variável em `Settings > Config Vars`.

## O que a integração faz

- inicializa o SDK no startup da aplicação;
- captura exceções não tratadas em nível de FastAPI;
- envia notificações manuais para:
  - upload de arquivos `.apkg`;
  - importação de cartões CSV;
  - sincronização de baralhos;
  - operações críticas de banco e publicação de releases;
- inclui contexto útil, como:
  - `request_id`;
  - `endpoint`;
  - `method`;
  - `user_id`;
  - `deck_id`;
  - `card_id`;
  - `release_id`;
  - parâmetros de operação relevantes.

Dados sensíveis, como senhas, tokens e payloads completos, não devem ser
enviados ao Honeybadger.

## Como testar

1. Configure `HONEYBADGER_API_KEY` no ambiente.
2. Inicie a aplicação.
3. Dispare uma falha controlada em um fluxo crítico, por exemplo:
   - subir um `.apkg` inválido;
   - enviar um CSV malformado;
   - forçar uma sincronização com estado inconsistente.
4. Verifique o erro no painel do Honeybadger.

## Onde ver os erros

Abra o painel do projeto no Honeybadger e consulte:

- lista de eventos;
- stack trace;
- tags;
- contexto da exceção;
- request ID associado ao erro.

## Validação local

Para validar a configuração sem esperar um erro real de produção, você pode:

1. configurar uma chave válida;
2. chamar manualmente `honeybadger.notify(...)` em um caminho de teste;
3. confirmar a chegada do evento no painel.

