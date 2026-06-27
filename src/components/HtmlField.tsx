import { Code } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import { cn } from '../lib/utils'
import { renderCloze, sanitizeHtml } from '../lib/html'

/**
 * Campos do Anki são HTML. Estes componentes espelham o editor do Anki:
 * uma visão formatada (HTML renderizado) e um toggle `<>` que revela o
 * código-fonte HTML. Todo HTML renderizado é sanitizado (ver lib/html).
 */

const sourceClass =
  'block max-h-[360px] overflow-auto whitespace-pre-wrap break-words rounded-[6px] border border-mu-border bg-mu-bg px-3 py-2.5 font-mono text-[13px] leading-[1.6] text-mu-text'

const toggleClass =
  'inline-flex h-7 w-7 items-center justify-center rounded-[5px] border border-transparent text-mu-muted-2 transition-colors hover:border-mu-border hover:bg-mu-surface-2 hover:text-mu-text aria-pressed:border-mu-brand aria-pressed:bg-mu-brand-bg aria-pressed:text-mu-brand'

/** Visão somente-leitura de um campo: HTML renderizado + toggle `<>` p/ fonte. */
export function HtmlFieldView({ label, value }: { label: string; value: string }) {
  const [showSource, setShowSource] = useState(false)
  return (
    <article className="rounded-[8px] border border-mu-border bg-mu-bg p-5">
      <header className="mb-2 flex items-center justify-between gap-2">
        <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-mu-muted-2">
          {label}
        </span>
        <button
          type="button"
          onClick={() => setShowSource((current) => !current)}
          aria-pressed={showSource}
          aria-label={showSource ? `Ver ${label} formatado` : `Ver HTML de ${label}`}
          title={showSource ? 'Ver formatado' : 'Ver HTML'}
          className={toggleClass}
        >
          <Code size={15} weight="bold" />
        </button>
      </header>
      {showSource ? (
        <code className={sourceClass}>{value}</code>
      ) : (
        <div
          className="text-[15px] leading-[1.65] text-mu-text [&_a]:text-mu-brand [&_a]:underline [&_img]:max-w-full [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:list-disc [&_ul]:pl-5"
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(renderCloze(value)) }}
        />
      )}
    </article>
  )
}

type ToolbarItem = { icon: React.ReactNode; label: string; cmd: string; arg?: string }

/**
 * Editor de um campo HTML: contenteditable WYSIWYG + toggle `<>` para editar o
 * código-fonte. Os dois modos compartilham o mesmo valor (string HTML).
 */
export function HtmlFieldEditor({
  label,
  value,
  onChange,
  toolbar,
  cloze = false,
  minHeight = 112,
}: {
  label: string
  value: string
  onChange: (next: string) => void
  toolbar: ToolbarItem[]
  cloze?: boolean
  minHeight?: number
}) {
  const [mode, setMode] = useState<'rich' | 'source'>('rich')
  const editorRef = useRef<HTMLDivElement>(null)

  // Sincroniza o DOM do contenteditable a partir do valor apenas ao (re)entrar
  // no modo rich — escrever innerHTML a cada render resetaria o cursor.
  useEffect(() => {
    if (mode === 'rich' && editorRef.current && editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode])

  function exec(cmd: string, arg?: string) {
    editorRef.current?.focus()
    if (cmd === 'createLink') {
      const url = window.prompt('URL do link:', 'https://')
      if (!url) return
      document.execCommand(cmd, false, url)
    } else {
      document.execCommand(cmd, false, arg)
    }
    onChange(editorRef.current?.innerHTML ?? '')
  }

  // Cloze: envolve a seleção em `{{cN::...}}`. `first` é sempre c1; `next` é a
  // continuação — próximo número após o maior já presente (c1 → c2 → c3…).
  function insertCloze(kind: 'first' | 'next') {
    const editor = editorRef.current
    if (!editor) return
    editor.focus()
    const selected = window.getSelection()?.toString() ?? ''
    const nums = [...editor.innerHTML.matchAll(/\{\{c(\d+)::/g)].map((m) => Number(m[1]))
    const max = nums.length ? Math.max(...nums) : 0
    const n = kind === 'first' ? 1 : max + 1
    document.execCommand('insertText', false, `{{c${n}::${selected || '...'}}}`)
    onChange(editor.innerHTML)
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[14px] font-semibold text-mu-text">{label}</span>
        <button
          type="button"
          onClick={() => setMode((current) => (current === 'rich' ? 'source' : 'rich'))}
          aria-pressed={mode === 'source'}
          aria-label={mode === 'source' ? `Editar ${label} formatado` : `Editar HTML de ${label}`}
          title={mode === 'source' ? 'Editar formatado' : 'Editar HTML'}
          className={toggleClass}
        >
          <Code size={15} weight="bold" />
        </button>
      </div>

      {mode === 'rich' && (
        <div
          className="flex flex-wrap items-center gap-0.5 rounded-[6px] border border-mu-border bg-mu-bg p-1"
          aria-label={`Barra de formatação de ${label}`}
        >
          {toolbar.map((item, index) => (
            <button
              key={index}
              type="button"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => exec(item.cmd, item.arg)}
              aria-label={item.label}
              title={item.label}
              className="inline-flex h-7 min-w-7 items-center justify-center rounded-[4px] px-1 text-mu-muted transition-colors hover:bg-mu-border-hover hover:text-mu-text"
            >
              {item.icon}
            </button>
          ))}
          {cloze && (
            <>
              <span className="mx-0.5 h-5 w-px bg-mu-border" aria-hidden />
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => insertCloze('first')}
                aria-label="Lacuna cloze c1"
                title="Cloze: c1"
                className="inline-flex h-7 min-w-7 items-center justify-center rounded-[4px] px-1.5 font-mono text-[12px] font-semibold text-mu-muted transition-colors hover:bg-mu-border-hover hover:text-mu-text"
              >
                [...]
              </button>
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => insertCloze('next')}
                aria-label="Próxima lacuna cloze (cN+1)"
                title="Cloze: próximo número (cN+1)"
                className="inline-flex h-7 min-w-7 items-center justify-center rounded-[4px] px-1.5 font-mono text-[12px] font-semibold text-mu-muted transition-colors hover:bg-mu-border-hover hover:text-mu-text"
              >
                [...]+
              </button>
            </>
          )}
        </div>
      )}

      {mode === 'rich' ? (
        <div
          ref={editorRef}
          contentEditable
          suppressContentEditableWarning
          role="textbox"
          aria-multiline="true"
          aria-label={label}
          onInput={() => onChange(editorRef.current?.innerHTML ?? '')}
          style={{ minHeight }}
          className="w-full rounded-[6px] border border-mu-border bg-mu-surface px-3.5 py-2.5 text-[15px] leading-[1.6] text-mu-text outline-none transition-colors focus:border-mu-brand [&_a]:text-mu-brand [&_a]:underline [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:list-disc [&_ul]:pl-5"
        />
      ) : (
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          spellCheck={false}
          style={{ minHeight }}
          className={cn(sourceClass, 'w-full resize-y outline-none focus:border-mu-brand')}
          aria-label={`HTML de ${label}`}
        />
      )}
    </div>
  )
}
