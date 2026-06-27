import { ChatText as MessageSquare } from '@phosphor-icons/react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiRequest } from '../../api/client'
import { useAuth } from '../../auth/auth-context'
import { formatDate } from '../../lib/presentation'
import { cn } from '../../lib/utils'
import type { NoteSuggestionCommentList } from '../../types'

const primaryBtn =
  'inline-flex h-[38px] items-center gap-2 rounded-[6px] bg-[#231651] px-4 text-[13px] font-semibold !text-white transition-colors hover:bg-[#1a1040] disabled:opacity-50'

export function SuggestionDiscussion({ suggestionId }: { suggestionId: string }) {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState('')

  const commentsQuery = useQuery({
    queryKey: ['suggestion-comments', suggestionId],
    queryFn: () =>
      apiRequest<NoteSuggestionCommentList>(
        `/note-suggestions/${suggestionId}/comments`,
        {},
        token,
      ),
  })

  const addComment = useMutation({
    mutationFn: (body: string) =>
      apiRequest(
        `/note-suggestions/${suggestionId}/comments`,
        { method: 'POST', body: JSON.stringify({ body }) },
        token,
      ),
    onSuccess: () => {
      setDraft('')
      queryClient.invalidateQueries({
        queryKey: ['suggestion-comments', suggestionId],
      })
    },
  })

  const comments = commentsQuery.data?.items ?? []

  return (
    <section className="rounded-[10px] border border-mu-border bg-mu-surface p-5">
      <div>
        <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-mu-brand">
          Discussão
        </span>
        <h2 className="mt-1.5 font-dm-serif text-[20px] font-normal text-mu-text">
          {comments.length
            ? `${comments.length} comentário${comments.length > 1 ? 's' : ''}`
            : 'Conversa da comunidade'}
        </h2>
      </div>

      <div className="mt-4 flex flex-col gap-2.5">
        {commentsQuery.isLoading ? (
          <p className="text-[13px] text-mu-muted">Carregando comentários...</p>
        ) : comments.length === 0 ? (
          <p className="text-[13px] text-mu-muted">
            Nenhum comentário ainda. Seja o primeiro a comentar.
          </p>
        ) : (
          comments.map((comment) => (
            <article
              key={comment.comment_id}
              className="rounded-[8px] border border-mu-border bg-mu-bg p-3.5"
            >
              <header className="flex items-center justify-between gap-2">
                <strong className="text-[13px] font-semibold text-mu-text">
                  {comment.author_email}
                </strong>
                <small className="text-[11px] text-mu-muted-2">
                  {formatDate(comment.created_at)}
                </small>
              </header>
              <p className="mt-1.5 whitespace-pre-wrap text-[13px] leading-[1.55] text-mu-text">
                {comment.body}
              </p>
            </article>
          ))
        )}
      </div>

      <label className="mt-4 flex flex-col gap-1.5">
        <span className="text-[13px] font-semibold text-mu-text">
          Adicionar comentário
        </span>
        <textarea
          rows={3}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Compartilhe sua opinião sobre esta sugestão."
          className="w-full resize-y rounded-[6px] border border-mu-border bg-mu-bg px-3 py-2 text-[14px] leading-[1.5] text-mu-text outline-none transition-colors placeholder:text-mu-muted-2 focus:border-mu-brand"
        />
      </label>
      {addComment.error && (
        <p className="mt-2 text-[12.5px] text-mu-danger">
          {addComment.error instanceof Error
            ? addComment.error.message
            : 'Falha ao publicar comentário.'}
        </p>
      )}
      <button
        type="button"
        disabled={!draft.trim() || addComment.isPending}
        onClick={() => addComment.mutate(draft.trim())}
        className={cn(primaryBtn, 'mt-3')}
      >
        <MessageSquare size={16} />
        Publicar comentário
      </button>
    </section>
  )
}
