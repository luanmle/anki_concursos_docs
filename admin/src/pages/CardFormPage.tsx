import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Eye, FloppyDisk as Save } from '@phosphor-icons/react'
import { useEffect, useMemo } from 'react'
import {
  useForm,
  useWatch,
  type FieldErrors,
  type UseFormRegister,
} from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import { ErrorState, LoadingState, PageHeader } from '../components/ui-primitives'
import type {
  CardDetail,
  CardVersion,
  DisciplineList,
  TopicList,
} from '../types'
import {
  cardCreateSchema,
  cardVersionSchema,
  type CardCreateValues,
  type CardVersionValues,
} from './card-form-schema'
type EditorValues = CardCreateValues | CardVersionValues
type ContentValues = Pick<
  CardCreateValues,
  'front_text' | 'back_text' | 'answer_text' | 'explanation_text'
>

const emptyContent: ContentValues = {
  front_text: '',
  back_text: '',
  answer_text: '',
  explanation_text: '',
}

export function NewCardPage() {
  const { token, user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const form = useForm<CardCreateValues>({
    resolver: zodResolver(cardCreateSchema),
    defaultValues: {
      card_kind: 'basic',
      canonical_key: '',
      discipline_id: '',
      topic_id: '',
      ...emptyContent,
      change_reason: 'Versão inicial',
    },
  })
  const values = useWatch({ control: form.control }) as CardCreateValues
  const cardKind = useWatch({ control: form.control, name: 'card_kind' })
  const disciplineId = useWatch({
    control: form.control,
    name: 'discipline_id',
  })
  const disciplines = useQuery({
    queryKey: ['disciplines'],
    queryFn: () => apiRequest<DisciplineList>('/disciplines', {}, token),
  })
  const topics = useQuery({
    queryKey: ['topics', disciplineId],
    queryFn: () =>
      apiRequest<TopicList>(
        `/disciplines/${disciplineId}/topics`,
        {},
        token,
      ),
    enabled: Boolean(disciplineId),
  })
  const mutation = useMutation({
    mutationFn: (payload: CardCreateValues) =>
      apiRequest<CardDetail>(
        '/cards',
        {
          method: 'POST',
          body: JSON.stringify({
            ...payload,
            created_by: user?.email ?? 'authenticated-user',
          }),
        },
        token,
      ),
    onSuccess: (card) => {
      queryClient.invalidateQueries({ queryKey: ['cards'] })
      form.reset(form.getValues())
      navigate(`/cards/${card.card_id}`, { replace: true })
    },
  })

  useEffect(() => {
    form.setValue('topic_id', '', { shouldDirty: Boolean(disciplineId) })
  }, [disciplineId, form])

  useUnsavedChanges(form.formState.isDirty)

  return (
    <CardFormLayout
      title="Novo cartão"
      description="Cadastre a identidade estável e a versão inicial do conteúdo."
      backTo="/cards"
      backLabel="Voltar para cartões"
      formError={mutation.error}
    >
      <form
        className="editor-form"
        onSubmit={form.handleSubmit((payload) => mutation.mutate(payload))}
      >
        <section className="form-section">
          <SectionTitle
            title="Classificação"
            description="A disciplina determina os assuntos disponíveis."
          />
          <div className="form-grid">
            <Field
              label="Chave canônica"
              error={form.formState.errors.canonical_key?.message}
              counter={values.canonical_key.length}
              maxLength={255}
            >
              <input
                maxLength={255}
                placeholder="Ex.: direito-constitucional-controle"
                {...form.register('canonical_key')}
              />
            </Field>
            <Field
              label="Tipo de cartao"
              error={form.formState.errors.card_kind?.message}
            >
              <select {...form.register('card_kind')}>
                <option value="basic">Basic</option>
                <option value="cloze">Cloze</option>
              </select>
            </Field>
            <Field
              label="Disciplina"
              error={form.formState.errors.discipline_id?.message}
            >
              <select
                disabled={disciplines.isLoading}
                {...form.register('discipline_id')}
              >
                <option value="">Selecione uma disciplina</option>
                {disciplines.data?.items.map((discipline) => (
                  <option
                    key={discipline.discipline_id}
                    value={discipline.discipline_id}
                  >
                    {discipline.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field
              label="Assunto"
              error={form.formState.errors.topic_id?.message}
            >
              <select
                disabled={!disciplineId || topics.isLoading}
                {...form.register('topic_id')}
              >
                <option value="">
                  {disciplineId
                    ? 'Selecione um assunto'
                    : 'Selecione primeiro a disciplina'}
                </option>
                {topics.data?.items.map((topic) => (
                  <option key={topic.topic_id} value={topic.topic_id}>
                    {topic.name}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          {(disciplines.error || topics.error) && (
            <InlineApiError error={disciplines.error || topics.error} />
          )}
        </section>

        <ContentEditor
          register={form.register as UseFormRegister<EditorValues>}
          errors={form.formState.errors}
          values={values}
          cardKind={cardKind}
        />

        <section className="form-section">
          <SectionTitle
            title="Registro editorial"
            description="O cartão será criado com status de revisão pendente."
          />
          <Field
            label="Motivo da criação"
            error={form.formState.errors.change_reason?.message}
            counter={values.change_reason.length}
            maxLength={2_000}
          >
            <textarea
              rows={3}
              maxLength={2_000}
              {...form.register('change_reason')}
            />
          </Field>
        </section>

        <FormActions
          cancelTo="/cards"
          isDirty={form.formState.isDirty}
          isSubmitting={mutation.isPending}
          submitLabel="Criar cartão"
        />
      </form>
    </CardFormLayout>
  )
}

export function NewCardVersionPage() {
  const { cardId = '' } = useParams()
  const { token, user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const cardQuery = useQuery({
    queryKey: ['card', cardId],
    queryFn: () => apiRequest<CardDetail>(`/cards/${cardId}`, {}, token),
    enabled: Boolean(cardId),
  })
  const form = useForm<CardVersionValues>({
    resolver: zodResolver(cardVersionSchema),
    defaultValues: {
      ...emptyContent,
      change_reason: '',
    },
  })
  const values = useWatch({ control: form.control }) as CardVersionValues
  const mutation = useMutation({
    mutationFn: (payload: CardVersionValues) =>
      apiRequest<CardVersion>(
        `/cards/${cardId}/versions`,
        {
          method: 'POST',
          body: JSON.stringify({
            ...payload,
            created_by: user?.email ?? 'authenticated-user',
          }),
        },
        token,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] })
      queryClient.invalidateQueries({ queryKey: ['cards'] })
      form.reset(form.getValues())
      navigate(`/cards/${cardId}`, { replace: true })
    },
  })

  useEffect(() => {
    const current = cardQuery.data?.current_version
    if (!current || form.formState.isDirty) return
    form.reset({
      front_text: current.front_text,
      back_text: current.back_text,
      answer_text: current.answer_text,
      explanation_text: current.explanation_text,
      change_reason: '',
    })
  }, [cardQuery.data, form, form.formState.isDirty])

  useUnsavedChanges(form.formState.isDirty)

  if (cardQuery.isLoading) return <LoadingState />
  if (cardQuery.error) {
    return (
      <ErrorState
        message={cardQuery.error.message}
        requestId={
          cardQuery.error instanceof ApiError
            ? cardQuery.error.requestId
            : null
        }
      />
    )
  }
  if (!cardQuery.data?.current_version) {
    return (
      <ErrorState message="O cartão não possui uma versão atual para servir de base." />
    )
  }

  const card = cardQuery.data
  return (
    <CardFormLayout
      title={`Nova versão de ${card.public_id}`}
      description="Revise o conteúdo e registre claramente o motivo da alteração."
      backTo={`/cards/${cardId}`}
      backLabel="Voltar para o cartão"
      formError={mutation.error}
    >
      <div className="version-preservation-notice">
        Você está criando uma nova versão. A versão atual permanecerá preservada
        no histórico.
      </div>
      <form
        className="editor-form"
        onSubmit={form.handleSubmit((payload) => mutation.mutate(payload))}
      >
        <ContentEditor
          register={form.register as UseFormRegister<EditorValues>}
          errors={form.formState.errors}
          values={values}
          cardKind={card.card_kind}
        />
        <section className="form-section">
          <SectionTitle
            title="Motivo da alteração"
            description="Este registro será exibido no histórico de versões."
          />
          <Field
            label="Motivo"
            error={form.formState.errors.change_reason?.message}
            counter={values.change_reason.length}
            maxLength={2_000}
          >
            <textarea
              rows={4}
              maxLength={2_000}
              placeholder="Descreva o que mudou e por quê."
              {...form.register('change_reason')}
            />
          </Field>
        </section>
        <FormActions
          cancelTo={`/cards/${cardId}`}
          isDirty={form.formState.isDirty}
          isSubmitting={mutation.isPending}
          submitLabel="Criar nova versão"
        />
      </form>
    </CardFormLayout>
  )
}

function CardFormLayout({
  title,
  description,
  backTo,
  backLabel,
  formError,
  children,
}: {
  title: string
  description: string
  backTo: string
  backLabel: string
  formError: Error | null
  children: React.ReactNode
}) {
  return (
    <div className="editor-page">
      <Link className="back-link" to={backTo}>
        <ArrowLeft size={16} />
        {backLabel}
      </Link>
      <PageHeader
        eyebrow="Fluxo editorial"
        title={title}
        description={description}
      />
      {formError && <InlineApiError error={formError} />}
      {children}
    </div>
  )
}

function ContentEditor({
  register,
  errors,
  values,
  cardKind,
}: {
  register: UseFormRegister<EditorValues>
  errors: FieldErrors<EditorValues>
  values: ContentValues
  cardKind?: 'basic' | 'cloze'
}) {
  const isCloze = cardKind === 'cloze'
  const preview = useMemo(
    () => [
      [isCloze ? 'Texto cloze' : 'Frente', values.front_text],
      ['Resposta', values.answer_text],
      [isCloze ? 'Extra' : 'Verso', values.back_text],
      ['Explicação', values.explanation_text],
    ],
    [
      isCloze,
      values.answer_text,
      values.back_text,
      values.explanation_text,
      values.front_text,
    ],
  )

  return (
    <section className="form-section">
      <SectionTitle
        title="Conteúdo pedagógico"
        description="Todos os quatro campos são obrigatórios para publicação."
      />
      <div className="editor-split">
        <div className="content-fields">
          <Field
            label="Frente / questão"
            error={errors.front_text?.message}
            counter={values.front_text.length}
            maxLength={20_000}
          >
            <textarea
              rows={6}
              maxLength={20_000}
              {...register('front_text')}
            />
          </Field>
          <Field
            label="Resposta"
            error={errors.answer_text?.message}
            counter={values.answer_text.length}
            maxLength={20_000}
          >
            <textarea
              rows={4}
              maxLength={20_000}
              {...register('answer_text')}
            />
          </Field>
          <Field
            label="Verso"
            error={errors.back_text?.message}
            counter={values.back_text.length}
            maxLength={20_000}
          >
            <textarea
              rows={5}
              maxLength={20_000}
              {...register('back_text')}
            />
          </Field>
          <Field
            label="Explicação"
            error={errors.explanation_text?.message}
            counter={values.explanation_text.length}
            maxLength={20_000}
          >
            <textarea
              rows={7}
              maxLength={20_000}
              {...register('explanation_text')}
            />
          </Field>
        </div>
        <aside className="content-preview">
          <div className="preview-heading">
            <Eye size={17} />
            <strong>Preview</strong>
          </div>
          {preview.map(([label, value]) => (
            <div key={label} className="preview-block">
              <span>{label}</span>
              <p>{value || 'O conteúdo aparecerá aqui.'}</p>
            </div>
          ))}
        </aside>
      </div>
    </section>
  )
}

function Field({
  label,
  error,
  counter,
  maxLength,
  children,
}: {
  label: string
  error?: string
  counter?: number
  maxLength?: number
  children: React.ReactNode
}) {
  return (
    <label className="form-field">
      <span className="field-heading">
        <strong>{label}</strong>
        {counter !== undefined && maxLength !== undefined && (
          <small>
            {counter.toLocaleString('pt-BR')} /{' '}
            {maxLength.toLocaleString('pt-BR')}
          </small>
        )}
      </span>
      {children}
      {error && <small className="field-error">{error}</small>}
    </label>
  )
}

function SectionTitle({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <div className="form-section-heading">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  )
}

function FormActions({
  cancelTo,
  isDirty,
  isSubmitting,
  submitLabel,
}: {
  cancelTo: string
  isDirty: boolean
  isSubmitting: boolean
  submitLabel: string
}) {
  const navigate = useNavigate()
  function cancel() {
    if (
      isDirty &&
      !window.confirm('Descartar as alterações não salvas desta página?')
    ) {
      return
    }
    navigate(cancelTo)
  }

  return (
    <footer className="form-actions">
      <button className="button button-secondary" type="button" onClick={cancel}>
        Cancelar
      </button>
      <button className="button button-primary" disabled={isSubmitting}>
        <Save size={17} />
        {isSubmitting ? 'Salvando…' : submitLabel}
      </button>
    </footer>
  )
}

function InlineApiError({ error }: { error: Error | null }) {
  if (!error) return null
  return (
    <div className="form-alert" role="alert">
      <strong>Não foi possível salvar.</strong>
      <span>{error.message}</span>
      {error instanceof ApiError && error.requestId && (
        <small>ID da requisição: {error.requestId}</small>
      )}
    </div>
  )
}

function useUnsavedChanges(enabled: boolean) {
  useEffect(() => {
    if (!enabled) return
    const preventUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault()
    }
    window.addEventListener('beforeunload', preventUnload)
    return () => window.removeEventListener('beforeunload', preventUnload)
  }, [enabled])
}
