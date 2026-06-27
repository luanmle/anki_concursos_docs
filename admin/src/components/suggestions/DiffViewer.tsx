import { Code } from '@phosphor-icons/react'
import { useState } from 'react'
import { renderCloze, sanitizeHtml } from '../../lib/html'
import { cn } from '../../lib/utils'
import { normalizeFieldDiff } from './diff'

/**
 * Diff de uma sugestão de nota: por campo mostra o estado Atual (vermelho) e o
 * Sugerido (verde), no estilo do AnkiHub. Campos do Anki são HTML — todo valor
 * é sanitizado antes de renderizar (ver lib/html), suportando texto, tags e
 * imagens. Também renderiza o diff de tags (adicionadas/removidas).
 */

function FieldHtml({ value }: { value: string }) {
  if (!value.trim()) {
    return <span className="text-[13px] italic text-mu-muted-2">(vazio)</span>
  }
  return (
    <div
      className="text-[14px] leading-[1.6] text-mu-text [&_a]:underline [&_img]:my-1 [&_img]:max-w-full [&_img]:rounded-[4px] [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:list-disc [&_ul]:pl-5"
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(renderCloze(value)) }}
    />
  )
}

const sideClass =
  'flex-1 rounded-[8px] border p-3.5'

function DiffPanel({
  heading,
  value,
  tone,
}: {
  heading: string
  value: string
  tone: 'current' | 'suggested'
}) {
  const [showSource, setShowSource] = useState(false)
  return (
    <div
      className={cn(
        sideClass,
        tone === 'current'
          ? 'border-mu-danger-border bg-mu-danger-bg'
          : 'border-mu-validated-border bg-mu-validated-bg',
      )}
    >
      <header className="mb-2 flex items-center justify-between gap-2">
        <span
          className={cn(
            'text-[11px] font-bold uppercase tracking-[0.08em]',
            tone === 'current' ? 'text-mu-danger' : 'text-mu-validated',
          )}
        >
          {heading}
        </span>
        {value.trim() && (
          <button
            type="button"
            onClick={() => setShowSource((s) => !s)}
            aria-pressed={showSource}
            title={showSource ? 'Ver formatado' : 'Ver HTML'}
            className="inline-flex h-6 w-6 items-center justify-center rounded-[5px] text-mu-muted-2 transition-colors hover:bg-mu-surface-2 hover:text-mu-text aria-pressed:text-mu-text"
          >
            <Code size={14} weight="bold" />
          </button>
        )}
      </header>
      {showSource ? (
        <code className="block max-h-[300px] overflow-auto whitespace-pre-wrap break-words rounded-[6px] bg-mu-bg/60 px-2.5 py-2 font-mono text-[12.5px] leading-[1.55] text-mu-text">
          {value}
        </code>
      ) : (
        <FieldHtml value={value} />
      )}
    </div>
  )
}

export function DiffViewer({
  fields,
  addedTags,
  removedTags,
}: {
  fields: Record<string, unknown>
  addedTags: string[]
  removedTags: string[]
}) {
  const fieldNames = Object.keys(fields ?? {})
  const hasTagChanges = addedTags.length > 0 || removedTags.length > 0

  if (fieldNames.length === 0 && !hasTagChanges) {
    return (
      <p className="text-[13px] text-mu-muted">Sem alterações em campos.</p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {fieldNames.map((name) => {
        const diff = normalizeFieldDiff(fields[name])
        return (
          <div key={name} className="flex flex-col gap-1.5">
            <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-mu-muted-2">
              {name}
            </span>
            <div className="flex flex-col gap-2.5 sm:flex-row">
              <DiffPanel heading="Atual" value={diff.old} tone="current" />
              <DiffPanel heading="Sugerido" value={diff.new} tone="suggested" />
            </div>
          </div>
        )
      })}

      {hasTagChanges && (
        <div className="flex flex-col gap-1.5">
          <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-mu-muted-2">
            Tags
          </span>
          <div className="flex flex-wrap gap-1.5">
            {removedTags.map((tag) => (
              <span
                key={`r-${tag}`}
                className="rounded-[5px] border border-mu-danger-border bg-mu-danger-bg px-2 py-1 text-[12px] font-medium text-mu-danger line-through"
              >
                {tag}
              </span>
            ))}
            {addedTags.map((tag) => (
              <span
                key={`a-${tag}`}
                className="rounded-[5px] border border-mu-validated-border bg-mu-validated-bg px-2 py-1 text-[12px] font-medium text-mu-validated"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
