import { useQuery } from '@tanstack/react-query'
import { CheckCircle as CheckCircle2, Database, ArrowClockwise as RefreshCw, Cloud as Server } from '@phosphor-icons/react'
import { API_URL, apiRequest } from '../api/client'
import { PageHeader } from '../components/ui'

async function getOperationStatus() {
  const health = await apiRequest<{ status: string }>('/health')
  const ready = await apiRequest<{ status: string; database: string }>('/ready')
  return { health, ready, checkedAt: new Date() }
}

export function OperationPage() {
  const query = useQuery({
    queryKey: ['operation'],
    queryFn: getOperationStatus,
    retry: false,
  })

  return (
    <>
      <PageHeader
        title="Operação"
        description="Disponibilidade da API e da conexão com o banco de dados."
        action={
          <button className="button button-secondary" onClick={() => query.refetch()}>
            <RefreshCw size={17} /> Atualizar
          </button>
        }
      />
      <div className="operation-grid">
        <StatusCard
          icon={<Server />}
          title="API"
          status={query.isError ? 'Indisponível' : query.data ? 'Disponível' : 'Verificando'}
          healthy={Boolean(query.data)}
        />
        <StatusCard
          icon={<Database />}
          title="PostgreSQL"
          status={query.data?.ready.database === 'ok' ? 'Disponível' : query.isError ? 'Indisponível' : 'Verificando'}
          healthy={query.data?.ready.database === 'ok'}
        />
      </div>
      <section className="operation-detail">
        <div>
          <span>URL base da API</span>
          <code>{API_URL}</code>
        </div>
        <div>
          <span>Ambiente do frontend</span>
          <strong>
            {window.__APP_CONFIG__?.APP_ENV ||
              import.meta.env.VITE_APP_ENV ||
              'STAGING'}
          </strong>
        </div>
        <div>
          <span>Última verificação</span>
          <strong>{query.data?.checkedAt.toLocaleString('pt-BR') || 'Em andamento'}</strong>
        </div>
      </section>
    </>
  )
}

function StatusCard({
  icon,
  title,
  status,
  healthy,
}: {
  icon: React.ReactNode
  title: string
  status: string
  healthy: boolean
}) {
  return (
    <article className="status-card">
      <span className="status-icon">{icon}</span>
      <div>
        <span>{title}</span>
        <strong>{status}</strong>
      </div>
      {healthy && <CheckCircle2 className="status-ok" />}
    </article>
  )
}
