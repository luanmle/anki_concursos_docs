import {
  Activity,
  ArrowRight,
  BookOpenCheck,
  CircleCheck,
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
        eyebrow="Console administrativo"
        title="Visão geral"
        description={`Olá, ${user?.display_name.split(' ')[0]}. Acesse o fluxo editorial e as áreas disponíveis para o seu papel.`}
      />
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
      <section className="dashboard-lower-grid">
        <article className="workflow-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Processo controlado</p>
              <h2>Fluxo editorial padrão</h2>
            </div>
            <GitBranch size={21} />
          </div>
          <div className="workflow-steps">
            {[
              ['Cadastrar', 'Criar o cartão e sua versão inicial.'],
              ['Revisar', 'Conferir conteúdo, referência e explicação.'],
              ['Aprovar', 'Registrar a decisão editorial.'],
              ['Publicar', 'Promover uma versão aprovada.'],
              ['Distribuir', 'Adicionar ao deck e publicar uma release.'],
            ].map(([step, description], index) => (
              <div key={step}>
                <b>{index + 1}</b>
                <span>
                  <strong>{step}</strong>
                  <small>{description}</small>
                </span>
              </div>
            ))}
          </div>
        </article>
        <article className="principle-card">
          <CircleCheck size={22} />
          <div>
            <p className="eyebrow">Integridade garantida</p>
            <strong>Versões publicadas são imutáveis</strong>
            <p>
              Toda mudança pedagógica cria uma nova versão. O histórico anterior
              permanece disponível para auditoria e sincronização.
            </p>
          </div>
        </article>
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
