import type { ReactNode } from 'react'
import { translateStatus } from '../lib/presentation'

export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`status-badge status-${value}`} title={value} aria-label={value}>
      {translateStatus(value)}
    </span>
  )
}

export function PageHeader({
  title,
  description,
  action,
  eyebrow = 'Administração',
}: {
  title: string
  description: string
  action?: ReactNode
  eyebrow?: string
}) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action}
    </header>
  )
}

export function EmptyState({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  )
}

export function LoadingState() {
  return (
    <div className="loading-state" aria-live="polite">
      <span className="spinner" />
      Carregando dados...
    </div>
  )
}

export function ErrorState({
  message,
  requestId,
}: {
  message: string
  requestId?: string | null
}) {
  return (
    <div className="error-state" role="alert">
      <strong>Não foi possível carregar esta área.</strong>
      <p>{message}</p>
      {requestId && <small>ID da requisição: {requestId}</small>}
    </div>
  )
}
