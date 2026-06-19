# ADR-0005 — JWT HS256 implementado sem biblioteca externa

**Status:** Aceito
**Data:** 2026-06-15

## Contexto

O projeto precisa de autenticação por token para a API. A abordagem padrão seria usar `python-jose` ou `PyJWT`, mas ambas adicionam dependências e têm histórico de vulnerabilidades (e.g., CVE-2022-29217 no PyJWT).

## Decisão

JWT HS256 implementado diretamente com `hmac`, `hashlib` e `base64` da stdlib (`app/core/security.py:69-149`). O token contém `sub`, `email`, `role`, `ver` (credential_version), `token_type`, `iat`, `exp`. A revogação é feita comparando `ver` do token com `user.credential_version` no banco — incrementar `credential_version` invalida todos os tokens emitidos.

Senhas armazenadas com PBKDF2-HMAC-SHA256, 600.000 iterações, salt aleatório de 16 bytes (`app/core/security.py:39-50`).

## Consequências

- **Positivas:** zero dependências externas de criptografia; controle total sobre o formato do token; revogação granular por usuário.
- **Negativas:** a implementação custom precisa ser mantida manualmente; não aproveita validações de campo que bibliotecas maduras já oferecem.
- **Neutras:** existe suporte legado a `X-Admin-API-Key` para integrações fora de produção (`app/core/security.py:219-229`), controlado por `allow_legacy_admin_api_key`.

## Alternativas consideradas

- **`python-jose` / `PyJWT`:** descartados pela adição de dependência e histórico de CVEs.
- **OAuth2 externo:** TODO(confirmar): foi cogitado para integrações futuras com SSO?
