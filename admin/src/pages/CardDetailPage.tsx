import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  CheckCircle as CheckCircle2,
  GitBranch,
  ClockClockwise as History,
  Plus,
  PaperPlaneRight as Send,
} from '@phosphor-icons/react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import {
  ErrorState,
  LoadingState,
  StatusBadge,
} from '../components/ui-primitives'
import { formatDate } from '../lib/presentation'
import type { CardDetail } from '../types'

export function CardDetailPage() {
  const { cardId = '' } = useParams()
  const { token, hasRole } = useAuth()
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['card', cardId],
    queryFn: () => apiRequest<CardDetail>(`/cards/${cardId}`, {}, token),
    enabled: Boolean(cardId),
  })
  const action = useMutation({
    mutationFn: ({
      versionId,
      operation,
    }: {
      versionId: string
      operation: 'approve' | 'publish'
    }) =>
      apiRequest<CardDetail>(
        `/cards/${cardId}/versions/${versionId}/${operation}`,
        { method: 'POST' },
        token,
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(['card', cardId], data)
      queryClient.invalidateQueries({ queryKey: ['cards'] })
    },
  })

  if (query.isLoading) return <LoadingState />
  if (query.error) {
    return (
      <ErrorState
        message={query.error.message}
        requestId={query.error instanceof ApiError ? query.error.requestId : null}
      />
    )
  }
  if (!query.data) return null

  const card = query.data
  const current = card.current_version
  const canReview = hasRole('admin', 'reviewer')
  const canCreateVersion = hasRole('admin', 'curator')

  return (
    <div className="card-detail-page">
      <Link className="back-link" to="/cards">
        <ArrowLeft size={16} />
        Voltar para cartões
      </Link>
      <header className="detail-header">
        <div>
          <div className="detail-kicker">
            <code>{card.public_id}</code>
            <StatusBadge value={card.status} />
          </div>
          <h1>{card.canonical_key}</h1>
          <p>
            Versão atual {current ? `v${current.version_number}` : 'não definida'} ·
            atualização {formatDate(card.updated_at)}
          </p>
        </div>
        <div className="detail-actions">
          {canCreateVersion && (
            <Link
              className="button button-primary"
              to={`/cards/${card.card_id}/versions/new`}
            >
              <Plus size={17} />
              Nova versão
            </Link>
          )}
        </div>
      </header>

      {action.error && (
        <ErrorState
          message={action.error.message}
          requestId={
            action.error instanceof ApiError ? action.error.requestId : null
          }
        />
      )}

      <div className="detail-layout">
        <main className="detail-content">
          {current ? (
            <>
              <ContentBlock label="Frente / questão" content={current.front_text} />
              <ContentBlock
                label="Resposta"
                content={current.answer_text}
                accent="success"
              />
              <ContentBlock
                label="Verso"
                content={current.back_text}
              />
              <ContentBlock
                label="Explicação detalhada"
                content={current.explanation_text}
              />
            </>
          ) : (
            <section className="empty-state">
              <strong>Este cartão ainda não possui versão atual.</strong>
            </section>
          )}
        </main>

        <aside className="detail-sidebar">
          <section className="metadata-card">
            <p className="eyebrow">Metadados</p>
            <dl>
              <div>
                <dt>Card ID</dt>
                <dd><code>{card.card_id}</code></dd>
              </div>
              <div>
                <dt>Disciplina</dt>
                <dd><code>{card.discipline_id}</code></dd>
              </div>
              <div>
                <dt>Assunto</dt>
                <dd><code>{card.topic_id}</code></dd>
              </div>
              {current && (
                <>
                  <div>
                    <dt>Status da versão</dt>
                    <dd><StatusBadge value={current.status} /></dd>
                  </div>
                  <div>
                    <dt>Criada por</dt>
                    <dd>{current.created_by}</dd>
                  </div>
                </>
              )}
            </dl>
          </section>

          {current && canReview && (
            <section className="editorial-actions">
              <p className="eyebrow">Decisão editorial</p>
              {current.status === 'needs_review' && (
                <button
                  className="button button-primary"
                  disabled={action.isPending}
                  onClick={() =>
                    action.mutate({
                      versionId: current.card_version_id,
                      operation: 'approve',
                    })
                  }
                >
                  <CheckCircle2 size={17} />
                  Aprovar versão
                </button>
              )}
              {current.status === 'approved' && (
                <button
                  className="button button-success"
                  disabled={action.isPending}
                  onClick={() =>
                    action.mutate({
                      versionId: current.card_version_id,
                      operation: 'publish',
                    })
                  }
                >
                  <Send size={17} />
                  Publicar versão
                </button>
              )}
              {!['needs_review', 'approved'].includes(current.status) && (
                <p className="muted-copy">
                  Nenhuma ação editorial disponível para este estado.
                </p>
              )}
            </section>
          )}
        </aside>
      </div>

      <section className="history-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Auditabilidade</p>
            <h2>Histórico de versões</h2>
          </div>
          <History size={21} />
        </div>
        <div className="version-history">
          {card.versions.map((version) => (
            <article key={version.card_version_id}>
              <span className="history-icon"><GitBranch size={16} /></span>
              <div>
                <strong>Versão {version.version_number}</strong>
                <p>{version.change_reason}</p>
                <small>
                  {version.created_by} · {formatDate(version.created_at)}
                </small>
              </div>
              <StatusBadge value={version.status} />
              {canReview && version.status === 'needs_review' && (
                <button
                  className="button button-primary"
                  disabled={action.isPending}
                  onClick={() =>
                    action.mutate({
                      versionId: version.card_version_id,
                      operation: 'approve',
                    })
                  }
                >
                  <CheckCircle2 size={15} />
                  Aprovar
                </button>
              )}
              {canReview && version.status === 'approved' && (
                <button
                  className="button button-success"
                  disabled={action.isPending}
                  onClick={() =>
                    action.mutate({
                      versionId: version.card_version_id,
                      operation: 'publish',
                    })
                  }
                >
                  <Send size={15} />
                  Publicar
                </button>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function ContentBlock({
  label,
  content,
  accent,
}: {
  label: string
  content: string
  accent?: 'success'
}) {
  return (
    <section className={`content-block ${accent ? `content-${accent}` : ''}`}>
      <p className="eyebrow">{label}</p>
      <div>{content}</div>
    </section>
  )
}
