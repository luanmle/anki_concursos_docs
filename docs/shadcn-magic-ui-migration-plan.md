# Plano de Migração: shadcn/ui + Magic UI

**Data:** 2026-06-23  
**Escopo:** `admin/` (React 19 + Vite 8 + Tailwind 3.4.17 + npm)

---

## Contexto

O admin é um SPA React com CSS customizado monolítico (`index.css`, ~3075 linhas). A migração para shadcn/ui e Magic UI é **incremental** — os componentes existentes continuam funcionando em paralelo. Nenhuma tela é reescrita neste plano.

---

## Riscos Conhecidos

| Risco | Severidade | Mitigação |
|---|---|---|
| `src/components/ui.tsx` conflita com `src/components/ui/` (shadcn) | Crítico | Renomear antes de rodar o CLI |
| Variáveis CSS `--primary` (hex) colidem com shadcn (HSL) | Alto | Usar prefixo `--shad-*` ou escopo separado |
| TypeScript 6.0.2 pode travar o CLI do shadcn | Médio | Usar flag `--legacy-peer-deps`; testar primeiro |
| React 19 requer shadcn CLI ≥ 2.1 | Baixo | Fixar versão `npx shadcn@latest` |

---

## Fases

### Fase 1 — Resolver conflito de nomes

- [x] **1.1** Renomear `src/components/ui.tsx` → `src/components/ui-primitives.tsx` ✅
- [x] **1.2** Atualizar os 12 pontos de import (`./components/ui` → `./components/ui-primitives`) ✅
- [x] **1.3** Confirmar build sem erros (`npm run build`) ✅ — 625 kB bundle, 0 erros

---

### Fase 2 — Configurar alias `@/`

- [x] **2.1** Adicionar `resolve.alias` em `vite.config.ts` ✅
- [x] **2.2** Adicionar `paths` + `baseUrl` + `ignoreDeprecations: "6.0"` em `tsconfig.app.json` ✅ (TS6 deprecou `baseUrl`; flag necessária para compatibilidade com shadcn CLI)
- [x] **2.3** Confirmar build sem erros (`npm run build`) ✅ — 0 erros

---

### Fase 3 — Inicializar shadcn/ui

- [x] **3.1** Rodar `npx shadcn@latest init -b radix -p nova -t vite --css-variables` ✅ (shadcn 4.11.0, preset Nova, Radix)
- [x] **3.2** Identificar e resolver incompatibilidade shadcn v4 + Tailwind v3 → **upgrade para Tailwind v4** ✅
  - `tailwindcss@^3` → `tailwindcss@^4 @tailwindcss/vite`
  - `vite.config.ts`: adicionar plugin `@tailwindcss/vite`
  - `postcss.config.js`: esvaziado (PostCSS plugin não é mais necessário com @tailwindcss/vite)
  - `index.css`: `@tailwind base/components/utilities` → `@import "tailwindcss"`
  - Adicionado `@theme inline` mapeando vars CSS para utilitários Tailwind v4
- [x] **3.3** Corrigir bug do shadcn CLI criando `admin/@/` ao invés de `admin/src/` ✅
  - Arquivos movidos para `src/components/ui/` e `src/lib/`
  - `paths` adicionados ao `tsconfig.json` raiz para que CLI resolva `@/` corretamente
- [x] **3.4** Confirmar build sem erros (`npm run build`) ✅ — 625 kB JS + 78 kB CSS, 0 erros

**Nota:** shadcn Button e `cn` util estão em `src/components/ui/button.tsx` e `src/lib/utils.ts`.

---

### Fase 4 — Magic UI

- [x] **4.1** Instalar `framer-motion`: `npm install framer-motion` ✅ (v11+, React 19 compatível)
- [x] **4.2** Confirmar build sem erros (`npm run build`) ✅ — 0 erros
- [x] **4.3** Smoke test do shadcn CLI: `npx shadcn@latest add badge` → criou `src/components/ui/badge.tsx` ✅ (CLI resolve `@/` corretamente agora)

**Stack pronta para uso de componentes Magic UI.**

---

## Arquivos modificados

| Arquivo | Fase | Tipo de mudança |
|---|---|---|
| `admin/src/components/ui.tsx` | 1 | Renomeado para `ui-primitives.tsx` |
| `admin/src/App.tsx` | 1 | Import atualizado |
| `admin/src/pages/*.tsx` (11 arquivos) | 1 | Imports atualizados |
| `admin/vite.config.ts` | 2 | Alias `@/` adicionado |
| `admin/tsconfig.app.json` | 2 | `paths` adicionado |
| `admin/src/index.css` | 3 | Variáveis HSL shadcn appendadas |
| `admin/tailwind.config.ts` | 3 | Plugin `tailwindcss-animate` + extend shadcn |
| `admin/components.json` | 3 | Criado pelo CLI shadcn |
| `admin/src/lib/utils.ts` | 3 | Criado pelo CLI shadcn (`cn` helper) |
| `admin/src/components/ui/button.tsx` | 3 | Smoke test shadcn |
| `admin/package.json` | 3–4 | Novas dependências |
