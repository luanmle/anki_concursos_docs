import {
  Activity,
  ArrowRight,
  BookOpenCheck,
  FileWarning,
  GitBranch,
  Library,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/auth-context'
import { PageHeader } from '../components/ui'

export function DashboardPage() {
  const { user } = useAuth()
  return (
    <>
      <PageHeader
        title={`Olá, ${user?.display_name.split(' ')[0]}`}
        description="Acompanhe o fluxo editorial e acesse as áreas disponíveis para o seu papel."
      />
      <section className="workflow-banner">
        <div>
          <p className="eyebrow">Fluxo editorial</p>
          <h2>Do cadastro à distribuição, sem sobrescrever o histórico.</h2>
        </div>
        <div className="workflow-steps">
          {['Cadastrar', 'Revisar', 'Aprovar', 'Publicar', 'Distribuir'].map(
            (step, index) => (
              <span key={step}>
                <b>{index + 1}</b>
                {step}
              </span>
            ),
          )}
        </div>
      </section>
      <section className="quick-grid">
        <QuickLink
          to="/cards"
          icon={<Library />}
          title="Cartões"
          description="Consulte conteúdo, estados e histórico de versões."
        />
        <QuickLink
          to="/decks"
          icon={<BookOpenCheck />}
          title="Decks e releases"
          description="Organize versões publicadas e exporte snapshots."
        />
        <QuickLink
          to="/reports"
          icon={<FileWarning />}
          title="Reports"
          description="Revise problemas reportados sem alterar versões antigas."
        />
        <QuickLink
          to="/operation"
          icon={<Activity />}
          title="Operação"
          description="Verifique a disponibilidade da API e do banco."
        />
      </section>
      <section className="principle-card">
        <GitBranch size={24} />
        <div>
          <strong>Regra central de versionamento</strong>
          <p>
            Toda mudança pedagógica cria uma nova versão. Publicações anteriores
            permanecem disponíveis para auditoria.
          </p>
        </div>
      </section>
    </>
  )
}

function QuickLink({
  to,
  icon,
  title,
  description,
}: {
  to: string
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <Link className="quick-link" to={to}>
      <span className="quick-icon">{icon}</span>
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
      <ArrowRight size={19} />
    </Link>
  )
}
