import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle2, Download, Upload, XCircle } from 'lucide-react'
import { useMemo, useState, type ChangeEvent, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import { ErrorState, PageHeader, StatusBadge } from '../components/ui'
import type { CardCsvImportResponse } from '../types'

const CSV_TEMPLATE = [
  'discipline,topic,front_text,back_text,answer_text,explanation_text,tags',
  'Direito Constitucional,Controle de constitucionalidade,"Pergunta do cartao","Verso do cartao","Resposta curta","Explicacao completa","tag1 tag2"',
].join('\n')

export function CardImportPage() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [csvText, setCsvText] = useState('')
  const [fileName, setFileName] = useState('')
  const [delimiter, setDelimiter] = useState(',')
  const [dryRun, setDryRun] = useState(true)
  const [defaultChangeReason, setDefaultChangeReason] =
    useState('Importacao CSV')

  const rowsPreview = useMemo(
    () => csvText.split(/\r?\n/).filter((line) => line.trim()).length,
    [csvText],
  )

  const mutation = useMutation({
    mutationFn: () =>
      apiRequest<CardCsvImportResponse>(
        '/card-imports/csv',
        {
          method: 'POST',
          body: JSON.stringify({
            csv_text: csvText,
            delimiter,
            dry_run: dryRun,
            default_change_reason: defaultChangeReason,
          }),
        },
        token,
      ),
    onSuccess: (data) => {
      if (!data.dry_run) {
        queryClient.invalidateQueries({ queryKey: ['cards'] })
        queryClient.invalidateQueries({ queryKey: ['card-count'] })
        queryClient.invalidateQueries({ queryKey: ['dashboard-cards'] })
      }
    },
  })

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    setCsvText(await file.text())
    mutation.reset()
  }

  function submitImport(event: FormEvent) {
    event.preventDefault()
    mutation.mutate()
  }

  function downloadTemplate() {
    const blob = new Blob([CSV_TEMPLATE], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'modelo-importacao-cartoes.csv'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const result = mutation.data
  const statusLabel = dryRun ? 'Validar CSV' : 'Importar cartoes'

  return (
    <div className="csv-import-page">
      <Link className="back-link" to="/cards">
        <ArrowLeft size={16} />
        Voltar para cartoes
      </Link>
      <PageHeader
        eyebrow="Importacao administrativa"
        title="Importar cartoes por CSV"
        description="Envie cartoes em lote sem informar IDs. A plataforma gera card_id, public_id, card_version_id e chave canonica, bloqueando duplicatas por conteudo."
        action={
          <button
            className="button button-secondary"
            type="button"
            onClick={downloadTemplate}
          >
            <Download size={17} />
            Baixar modelo
          </button>
        }
      />

      {mutation.error && (
        <ErrorState
          message={mutation.error.message}
          requestId={
            mutation.error instanceof ApiError
              ? mutation.error.requestId
              : null
          }
        />
      )}

      <form className="csv-import-layout" onSubmit={submitImport}>
        <section className="csv-import-card">
          <div className="section-heading">
            <p className="eyebrow">Arquivo</p>
            <h2>Selecionar CSV</h2>
            <p>
              Use nomes de disciplina e assunto ja cadastrados, ou informe
              discipline_id e topic_id. Os IDs dos cartoes nao devem aparecer
              no arquivo.
            </p>
          </div>

          <label className="file-drop-zone">
            <Upload size={26} />
            <strong>{fileName || 'Escolher arquivo .csv'}</strong>
            <span>
              Colunas minimas: discipline, topic, front_text, back_text,
              answer_text, explanation_text.
            </span>
            <input accept=".csv,text/csv" type="file" onChange={handleFileChange} />
          </label>

          <div className="csv-options-grid">
            <label>
              <span>Separador</span>
              <select
                value={delimiter}
                onChange={(event) => setDelimiter(event.target.value)}
              >
                <option value=",">Virgula (,)</option>
                <option value=";">Ponto e virgula (;)</option>
              </select>
            </label>
            <label>
              <span>Motivo padrao</span>
              <input
                value={defaultChangeReason}
                maxLength={2000}
                onChange={(event) =>
                  setDefaultChangeReason(event.target.value)
                }
              />
            </label>
          </div>

          <label className="dry-run-toggle">
            <input
              checked={dryRun}
              type="checkbox"
              onChange={(event) => setDryRun(event.target.checked)}
            />
            <span>
              Validar sem gravar no banco. Desmarque somente quando o resultado
              estiver correto.
            </span>
          </label>

          <div className="csv-import-actions">
            <button
              className="button button-primary"
              disabled={!csvText.trim() || mutation.isPending}
              type="submit"
            >
              {mutation.isPending ? 'Processando...' : statusLabel}
            </button>
            <span>{rowsPreview ? `${rowsPreview - 1} linhas detectadas` : ''}</span>
          </div>
        </section>

        <aside className="csv-rules-card">
          <p className="eyebrow">Regras</p>
          <h2>Como a plataforma evita duplicatas</h2>
          <ul>
            <li>O CSV nao precisa trazer card_id, public_id ou canonical_key.</li>
            <li>Conteudo identico gera o mesmo hash e entra como duplicado.</li>
            <li>Cartoes importados entram como needs_review.</li>
            <li>A coluna tags e aceita, mas ainda nao e gravada no banco.</li>
          </ul>
        </aside>
      </form>

      {result && <ImportResult data={result} />}
    </div>
  )
}

function ImportResult({ data }: { data: CardCsvImportResponse }) {
  const successfulLabel = data.dry_run ? 'Linhas validas' : 'Criados'
  return (
    <section className="csv-result-panel">
      <div className="csv-result-summary">
        <ResultMetric label="Total" value={data.total_rows} />
        <ResultMetric label={successfulLabel} value={data.created} />
        <ResultMetric label="Duplicados" value={data.duplicates} />
        <ResultMetric label="Erros" value={data.errors} />
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Linha</th>
              <th>Status</th>
              <th>Mensagem</th>
              <th>ID publico</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={`${item.row_number}-${item.status}`}>
                <td>{item.row_number}</td>
                <td>
                  <span className="csv-status-cell">
                    {item.status === 'error' ? (
                      <XCircle size={15} />
                    ) : (
                      <CheckCircle2 size={15} />
                    )}
                    <StatusBadge value={item.status} />
                  </span>
                </td>
                <td>{item.message}</td>
                <td>{item.public_id || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function ResultMetric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
