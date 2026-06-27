# Handoff: Migração Hero Muriae na ExplorePage

**Data:** 2026-06-25
**De:** Codex
**Para:** Claude Code
**Branch:** `frontend-redesign`
**Status:** em andamento

## Objetivo da próxima sessão

Continuar a migração gradual do design presente em `design-reference/`, partindo da ExplorePage e avançando para cards de baralho, filtros e shell visual.

## Estado atual

### O que foi feito

- Adicionado `admin/src/components/ExploreHero.tsx` com um componente dedicado para o Hero da ExplorePage.
- Atualizado `admin/src/pages/CommunityInterfacePages.tsx` para usar `ExploreHero` com o texto da referência `design-reference/redesign.html`.
- Atualizado `admin/src/index.css` com estilos Muriae escopados a `.ac-page-muriae`: sidebar de 264px, topbar de 64px, padding `48px 36px 72px`, fundo `#FAFAF8`, texto `#1F2430`, accent `#231651`, lede `#667085`.
- Adicionado fallback mobile em `admin/src/index.css` para evitar overflow horizontal abaixo de 720px.
- Adicionadas fontes locais em `admin/package.json`: `@fontsource-variable/dm-sans` e `@fontsource/dm-serif-display`.
- Usado shadcn MCP antes da implementação: `button` e `badge` foram verificados/instalados via `npx shadcn@latest add @shadcn/button @shadcn/badge`; o CLI pulou os arquivos porque já existiam.

### O que está pendente

- [ ] Migrar os cards de baralho da ExplorePage para o padrão do HTML estático.
- [ ] Migrar controles de filtro/ordenação conforme `design-reference/redesign.html`.
- [ ] Decidir se a shell inteira deve adotar Muriae agora ou se continuará escopada por página durante a migração.
- [ ] Corrigir mojibake restante em `admin/src/pages/CommunityInterfacePages.tsx` (`pÃºblicos`, `DisponÃ­veis`, etc.).

### Bloqueios

- Nenhum bloqueio técnico.

## Contexto técnico desta sessão

- **Decisão tomada:** manter equivalência visual em 800px com a referência, mas corrigir mobile real no projeto.
- **Invariante descoberta:** a referência estática em `http://127.0.0.1:8080/redesign.html` mantém a sidebar fixa em 390px e gera overflow horizontal; isso não deve ser copiado para produção.
- **Arquivo modificado:** `admin/src/index.css` — usa `:has(.ac-page-muriae)` para escopar mudanças de shell/wrapper só à ExplorePage migrada.
- **Arquivo modificado:** `admin/src/pages/CommunityInterfacePages.tsx` — o filtro saiu do Hero para preservar a composição da referência.

## Riscos desta tarefa

- `:has()` é usado para escopo visual; browsers modernos suportam, mas se houver alvo legado, considerar aplicar classe explícita no shell via rota.
- O lockfile já estava em transição na branch; `npm install` atualizou `admin/package-lock.json` além de adicionar as fontes.
- A migração ainda é parcial: a Hero está alinhada, mas cards, nav e textos abaixo ainda não estão idênticos à referência.

## Estado dos testes

```bash
cd admin
npm run build  # passou; apenas aviso de chunk > 500 kB
npm test       # passou: 3 arquivos, 8 testes
```

Validação visual feita com Playwright MCP:

```text
Referência: http://127.0.0.1:8080/redesign.html
Projeto:    http://localhost:5173/
Screenshot final: .playwright-mcp/localhost-5173-final-hero.png
Mobile corrigido: .playwright-mcp/current-after-hero-mobile-fixed.png
```

Métricas finais da Hero em 800x513:

```text
header:  x=300 y=112 w=464 h=164
eyebrow: font 12px, weight 600, color rgb(35, 22, 81)
h1:      DM Serif Display 42px, line-height 45.36px, color rgb(31, 36, 48)
lede:    DM Sans 17px, line-height 26.35px, color rgb(102, 112, 133)
```

## Comandos para retomar

```bash
git checkout frontend-redesign
cd admin
npm run dev -- --host 127.0.0.1
npm test
npm run build
```

## Skills sugeridas para a próxima sessão

- `interface-design` — para avaliar os próximos blocos visuais e manter consistência.
- `implement-with-tests` — se a próxima etapa alterar comportamento ou componentes com estado.
- `review-change` — antes do commit final ou PR.
- `document-changes` — ao concluir novo bloco migrado.
- `create-handoff` — se a migração continuar em outra sessão.
