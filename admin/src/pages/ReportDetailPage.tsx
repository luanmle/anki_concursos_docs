import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { WarningCircle as AlertTriangle, ArrowLeft, CheckCircle as CheckCircle2, GitBranch } from '@phosphor-icons/react'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import {
  ErrorState,
  LoadingState,
  StatusBadge,
} from '../components/ui-primitives'
import { formatDate, translateStatus } from '../lib/presentation'
import type { CardDetail, CardVersion, Report } from '../types'

type Decision = 'rejected' | 'duplicate' | 'converted_to_new_version'

interface ProposedVersion {
  front_text: string
  back_text: string
  answer_text: string
  explanation_text: string
  change_reason: string
}

const emptyVersion: ProposedVersion = {
  front_text: '',
  back_text: '',
  answer_text: '',
  explanation_text: '',
  change_reason: '',
}

export function ReportDetailPage() {
  const { reportId = '' } = useParams()
  const { token, user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [decision, setDecision] = useState<Decision>('rejected')
  const [comment, setComment] = useState('')
  const [evidenceReviewed, setEvidenceReviewed] = useState(false)
  const [proposed, setProposed] = useState<ProposedVersion>(emptyVersion)
  const report = useQuery({
    queryKey: ['report', reportId],
    queryFn: () =>
      apiRequest<Report>(`/admin/reports/${reportId}`, {}, token),
  })
  const card = useQuery({
    queryKey: ['card', report.data?.card_id],
    queryFn: () =>
      apiRequest<CardDetail>(`/cards/${report.data?.card_id}`, {}, token),
    enabled: Boolean(report.data?.card_id),
  })
  const reportedVersion = useMemo(
    () =>
      card.data?.versions.find(
        (version) => version.card_version_id === report.data?.card_version_id,
      ),
    [card.data?.versions, report.data?.card_version_id],
  )

  const review = useMutation({
    mutationFn: () =>
      apiRequest<Report>(
        `/admin/reports/${reportId}/review`,
        {
          method: 'POST',
          body: JSON.stringify({
            decision,
            reviewed_by: user?.email ?? 'authenticated-reviewer',
            admin_comment: comment.trim(),
            evidence_reviewed: evidenceReviewed,
            proposed_version:
              decision === 'converted_to_new_version' ? proposed : null,
          }),
        },
        token,
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(['report', reportId], data)
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      if (data.review_task.resulting_card_version_id) {
        queryClient.invalidateQueries({ queryKey: ['card', data.card_id] })
      }
    },
  })

  if (report.isLoading || card.isLoading) return <LoadingState />
  if (report.error || card.error) {
    const error = report.error || card.error
    return (
      <ErrorState
        message={error?.message || 'Não foi possível carregar o report.'}
        requestId={error instanceof ApiError ? error.requestId : null}
      />
    )
  }
  if (!report.data || !reportedVersion) return null

  const item = report.data
  const alreadyReviewed = item.review_task.status === 'completed'
  const conversionValid =
    decision !== 'converted_to_new_version' ||
    Object.values(proposed).every((value) => value.trim())
  const canSubmit = Boolean(comment.trim()) && conversionValid

  return (
    <div className="report-detail-page">
      <Link className="back-link" to="/reports">
        <ArrowLeft size={16} />
        Voltar para reports
      </Link>
      <header className="detail-header">
        <div>
          <div className="detail-kicker">
            <code>{item.report_id}</code>
            <StatusBadge value={item.status} />
          </div>
          <h1>Revisão de {item.public_id}</h1>
          <p>
            Versão reportada v{item.version_number} ·{' '}
            {translateStatus(item.report_type)}
          </p>
        </div>
        <Link className="button button-secondary" to={`/cards/${item.card_id}`}>
          Abrir cartão
        </Link>
      </header>

      {review.error && (
        <ErrorState
          message={review.error.message}
          requestId={
            review.error instanceof ApiError ? review.error.requestId : null
          }
        />
      )}

      <div className="report-layout">
        <main className="report-content">
          <section className="report-message">
            <p className="eyebrow">Mensagem do report</p>
            <blockquote>{item.message}</blockquote>
          </section>
          <section className="reported-version">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Conteúdo preservado</p>
                <h2>Versão reportada</h2>
              </div>
              <GitBranch size={20} />
            </div>
            <ReportedContent version={reportedVersion} />
          </section>
        </main>

        <aside className="report-review-column">
          <section className="metadata-card">
            <p className="eyebrow">Metadados do report</p>
            <dl>
              <div>
                <dt>Referência do usuário</dt>
                <dd>{item.reporter_reference || 'Não informada'}</dd>
              </div>
              <div>
                <dt>Recebido em</dt>
                <dd>{formatDate(item.created_at)}</dd>
              </div>
              <div>
                <dt>Status da tarefa</dt>
                <dd><StatusBadge value={item.review_task.status} /></dd>
              </div>
              {item.review_task.reviewed_at && (
                <div>
                  <dt>Revisado em</dt>
                  <dd>{formatDate(item.review_task.reviewed_at)}</dd>
                </div>
              )}
            </dl>
          </section>

          {alreadyReviewed ? (
            <section className="review-complete">
              <CheckCircle2 size={21} />
              <div>
                <strong>Revisão concluída</strong>
                <p>{item.review_task.admin_comment}</p>
                <StatusBadge value={item.review_task.decision || 'completed'} />
              </div>
            </section>
          ) : (
            <form
              className="review-form"
              onSubmit={(event) => {
                event.preventDefault()
                review.mutate()
              }}
            >
              <p className="eyebrow">Decisão de revisão</p>
              <label className="form-field">
                <span className="field-heading"><strong>Decisão</strong></span>
                <select
                  value={decision}
                  onChange={(event) => {
                    const nextDecision = event.target.value as Decision
                    setDecision(nextDecision)
                    if (
                      nextDecision === 'converted_to_new_version' &&
                      reportedVersion &&
                      !proposed.front_text
                    ) {
                      setProposed({
                        front_text: reportedVersion.front_text,
                        back_text: reportedVersion.back_text,
                        answer_text: reportedVersion.answer_text,
                        explanation_text: reportedVersion.explanation_text,
                        change_reason: '',
                      })
                    }
                  }}
                >
                  <option value="rejected">Rejeitar report</option>
                  <option value="duplicate">Marcar como duplicado</option>
                  <option value="converted_to_new_version">
                    Converter em nova versão
                  </option>
                </select>
              </label>
              <label className="form-field">
                <span className="field-heading">
                  <strong>Comentário administrativo</strong>
                  <small>{comment.length} / 5.000</small>
                </span>
                <textarea
                  rows={5}
                  value={comment}
                  maxLength={5_000}
                  onChange={(event) => setComment(event.target.value)}
                />
              </label>
              <label className="checkbox-field">
                <input
                  type="checkbox"
                  checked={evidenceReviewed}
                  onChange={(event) => setEvidenceReviewed(event.target.checked)}
                />
                <span>Evidência revisada</span>
              </label>

              {decision === 'converted_to_new_version' && (
                <div className="conversion-fields">
                  <div className="conversion-warning">
                    <AlertTriangle size={17} />
                    Uma nova versão será criada para revisão. A publicada não será
                    alterada.
                  </div>
                  <VersionFields value={proposed} onChange={setProposed} />
                </div>
              )}

              <div className="review-actions">
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => navigate('/reports')}
                >
                  Cancelar
                </button>
                <button
                  className="button button-primary"
                  disabled={!canSubmit || review.isPending}
                >
                  {review.isPending ? 'Enviando…' : 'Enviar revisão'}
                </button>
              </div>
            </form>
          )}
        </aside>
      </div>
    </div>
  )
}

function ReportedContent({ version }: { version: CardVersion }) {
  return (
    <div className="reported-content-grid">
      {[
        ['Frente / questão', version.front_text],
        ['Resposta', version.answer_text],
        ['Verso', version.back_text],
        ['Explicação', version.explanation_text],
      ].map(([label, content]) => (
        <div key={label}>
          <span>{label}</span>
          <p>{content}</p>
        </div>
      ))}
    </div>
  )
}

function VersionFields({
  value,
  onChange,
}: {
  value: ProposedVersion
  onChange: (value: ProposedVersion) => void
}) {
  const fields: Array<[keyof ProposedVersion, string, number]> = [
    ['front_text', 'Frente / questão', 4],
    ['answer_text', 'Resposta', 3],
    ['back_text', 'Verso', 4],
    ['explanation_text', 'Explicação', 5],
    ['change_reason', 'Motivo da alteração', 3],
  ]
  return (
    <>
      {fields.map(([field, label, rows]) => (
        <label className="form-field" key={field}>
          <span className="field-heading"><strong>{label}</strong></span>
          <textarea
            rows={rows}
            value={value[field]}
            onChange={(event) =>
              onChange({ ...value, [field]: event.target.value })
            }
          />
        </label>
      ))}
    </>
  )
}
