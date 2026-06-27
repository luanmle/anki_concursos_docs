import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle as CheckCircle2,
  Database,
  ArrowClockwise as RefreshCw,
  Cloud as Server,
} from '@phosphor-icons/react'
import { API_URL, apiRequest } from '../api/client'
import { ExploreHero } from '../components/ExploreHero'
import { cn } from '../lib/utils'

const muriaeSecondaryBtn =
  'inline-flex h-[42px] items-center gap-2 rounded-[6px] border border-mu-border bg-mu-surface px-4 text-[13.5px] font-semibold text-mu-text transition-colors hover:border-mu-border-hover hover:bg-mu-surface-2'
const muriaeSurface =
  'rounded-[10px] border border-mu-border bg-mu-surface shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.05)]'

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

  const environment =
    window.__APP_CONFIG__?.APP_ENV || import.meta.env.VITE_APP_ENV || 'STAGING'

  return (
    <div className="ac-page ac-page-muriae">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <ExploreHero
          eyebrow="Operação"
          title="Saúde do sistema"
          description="Disponibilidade da API e da conexão com o banco de dados."
        />
        <button
          type="button"
          className={cn(muriaeSecondaryBtn, 'shrink-0')}
          onClick={() => query.refetch()}
        >
          <RefreshCw size={17} />
          Atualizar
        </button>
      </div>

      <section className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatusCard
          icon={<Server size={22} />}
          title="API"
          status={
            query.isError ? 'Indisponível' : query.data ? 'Disponível' : 'Verificando'
          }
          healthy={Boolean(query.data)}
        />
        <StatusCard
          icon={<Database size={22} />}
          title="PostgreSQL"
          status={
            query.data?.ready.database === 'ok'
              ? 'Disponível'
              : query.isError
                ? 'Indisponível'
                : 'Verificando'
          }
          healthy={query.data?.ready.database === 'ok'}
        />
      </section>

      <section className={cn(muriaeSurface, 'mt-4 divide-y divide-mu-border')}>
        <DetailRow label="URL base da API">
          <code className="rounded-[5px] bg-mu-surface-2 px-2 py-1 font-mono text-[12.5px] text-mu-text">
            {API_URL}
          </code>
        </DetailRow>
        <DetailRow label="Ambiente do frontend">
          <strong className="text-[14px] font-semibold text-mu-text">
            {String(environment).toUpperCase()}
          </strong>
        </DetailRow>
        <DetailRow label="Última verificação">
          <strong className="text-[14px] font-semibold text-mu-text">
            {query.data?.checkedAt.toLocaleString('pt-BR') || 'Em andamento'}
          </strong>
        </DetailRow>
      </section>
    </div>
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
    <article
      className={cn(
        muriaeSurface,
        'flex items-center gap-4 p-5',
      )}
    >
      <span
        className={cn(
          'inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full',
          healthy
            ? 'bg-mu-validated-bg text-mu-validated'
            : 'bg-mu-brand-bg text-mu-brand',
        )}
      >
        {icon}
      </span>
      <div className="flex flex-col gap-0.5">
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-mu-muted-2">
          {title}
        </span>
        <strong className="text-[16px] font-semibold text-mu-text">{status}</strong>
      </div>
      {healthy && (
        <CheckCircle2
          size={22}
          weight="fill"
          className="ml-auto shrink-0 text-mu-validated"
        />
      )}
    </article>
  )
}

function DetailRow({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
      <span className="text-[13px] text-mu-muted">{label}</span>
      {children}
    </div>
  )
}
