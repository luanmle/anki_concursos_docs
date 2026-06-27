import DOMPurify from 'dompurify'

/**
 * Campos do Anki são HTML, vindos de sync/sugestões da comunidade — conteúdo
 * não confiável. Todo HTML renderizado na plataforma passa por estas funções.
 */

export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'b', 'strong', 'i', 'em', 'u', 's', 'strike', 'sub', 'sup', 'br', 'hr',
      'p', 'div', 'span', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4',
      'blockquote', 'code', 'pre', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
    ],
    ALLOWED_ATTR: ['href', 'title', 'style', 'src', 'alt', 'class', 'colspan', 'rowspan'],
    ALLOW_DATA_ATTR: false,
  })
}

/** Converte HTML do campo em texto puro (para previews/listas). */
export function htmlToText(html: string): string {
  const el = document.createElement('div')
  el.innerHTML = sanitizeHtml(html)
  return (el.textContent || '').replace(/\s+/g, ' ').trim()
}

/** Substitui marcação cloze `{{c1::resposta::dica}}` por destaque legível. */
export function renderCloze(html: string): string {
  return html.replace(
    /\{\{c\d+::(.*?)(?:::(.*?))?\}\}/g,
    (_match, answer: string) =>
      `<span class="rounded bg-mu-brand-bg px-1 font-semibold text-mu-brand">${answer}</span>`,
  )
}
