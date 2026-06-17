import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, KeyRound, Save, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import { ErrorState, LoadingState, PageHeader, StatusBadge } from '../components/ui'
import { formatDate } from '../lib/presentation'
import type { Paginated, User, UserRole } from '../types'

const createSchema = z
  .object({
    display_name: z.string().trim().min(1).max(255),
    email: z.string().trim().email(),
    role: z.enum(['admin', 'curator', 'reviewer', 'student']),
    password: z.string().min(12, 'Use pelo menos 12 caracteres.'),
    password_confirmation: z.string(),
  })
  .refine((value) => value.password === value.password_confirmation, {
    message: 'As senhas não conferem.',
    path: ['password_confirmation'],
  })

const editSchema = z.object({
  display_name: z.string().trim().min(1).max(255),
  role: z.enum(['admin', 'curator', 'reviewer', 'student']),
  is_active: z.boolean(),
})

type CreateValues = z.infer<typeof createSchema>
type EditValues = z.infer<typeof editSchema>

const rolePermissions: Record<UserRole, string[]> = {
  admin: [
    'Acesso administrativo completo',
    'Gerencia usuários e credenciais',
    'Cria, revisa e publica conteúdo',
  ],
  curator: [
    'Cria cartões e novas versões',
    'Compõe decks',
    'Consulta releases e exportações',
  ],
  reviewer: [
    'Aprova e publica versões',
    'Publica releases',
    'Revisa reports de usuários',
  ],
  student: [
    'Acessa o add-on do Anki',
    'Assina decks publicados',
    'Sincroniza cartoes assinados',
  ],
}

export function NewUserPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const form = useForm<CreateValues>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      display_name: '',
      email: '',
      role: 'curator',
      password: '',
      password_confirmation: '',
    },
  })
  const role = useWatch({ control: form.control, name: 'role' })
  const mutation = useMutation({
    mutationFn: (values: CreateValues) =>
      apiRequest<User>(
        '/admin/users',
        {
          method: 'POST',
          body: JSON.stringify({
            display_name: values.display_name,
            email: values.email,
            role: values.role,
            password: values.password,
          }),
        },
        token,
      ),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      navigate(`/users/${user.user_id}`, { replace: true })
    },
  })

  return (
    <UserLayout
      title="Novo usuário"
      description="Crie uma credencial administrativa e atribua o papel inicial."
      role={role}
      error={mutation.error}
    >
      <form
        className="user-form"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <section className="form-section">
          <div className="form-section-heading">
            <h2>Identidade e acesso</h2>
            <p>O e-mail será usado como identificador de login.</p>
          </div>
          <div className="user-form-grid">
            <UserField label="Nome de exibição" error={form.formState.errors.display_name?.message}>
              <input {...form.register('display_name')} />
            </UserField>
            <UserField label="E-mail" error={form.formState.errors.email?.message}>
              <input type="email" autoComplete="email" {...form.register('email')} />
            </UserField>
            <UserField label="Papel">
              <select {...form.register('role')}>
                <option value="admin">Administrador</option>
                <option value="curator">Curador</option>
                <option value="reviewer">Revisor</option>
                <option value="student">Estudante</option>
              </select>
            </UserField>
          </div>
        </section>
        <section className="form-section">
          <div className="form-section-heading">
            <h2>Senha inicial</h2>
            <p>Mínimo de 12 caracteres.</p>
          </div>
          <div className="user-form-grid two-columns">
            <UserField label="Senha" error={form.formState.errors.password?.message}>
              <input type="password" autoComplete="new-password" {...form.register('password')} />
            </UserField>
            <UserField
              label="Confirmar senha"
              error={form.formState.errors.password_confirmation?.message}
            >
              <input
                type="password"
                autoComplete="new-password"
                {...form.register('password_confirmation')}
              />
            </UserField>
          </div>
        </section>
        <UserActions pending={mutation.isPending} label="Criar usuário" />
      </form>
    </UserLayout>
  )
}

export function EditUserPage() {
  const { userId = '' } = useParams()
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const form = useForm<EditValues>({
    resolver: zodResolver(editSchema),
    defaultValues: { display_name: '', role: 'curator', is_active: true },
  })
  const users = useQuery({
    queryKey: ['users', 'lookup'],
    queryFn: () =>
      apiRequest<Paginated<User>>('/admin/users?page=1&page_size=100', {}, token),
  })
  const user = users.data?.items.find((item) => item.user_id === userId)
  const role = useWatch({ control: form.control, name: 'role' })
  const update = useMutation({
    mutationFn: (values: EditValues) =>
      apiRequest<User>(
        `/admin/users/${userId}`,
        { method: 'PATCH', body: JSON.stringify(values) },
        token,
      ),
    onSuccess: (data) => {
      queryClient.setQueryData<Paginated<User>>(['users', 'lookup'], (current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.user_id === data.user_id ? data : item,
              ),
            }
          : current,
      )
      queryClient.invalidateQueries({ queryKey: ['users'] })
      form.reset({
        display_name: data.display_name,
        role: data.role,
        is_active: data.is_active,
      })
    },
  })

  useEffect(() => {
    if (!user || form.formState.isDirty) return
    form.reset({
      display_name: user.display_name,
      role: user.role,
      is_active: user.is_active,
    })
  }, [form, form.formState.isDirty, user])

  if (users.isLoading) return <LoadingState />
  if (users.error) {
    return (
      <ErrorState
        message={users.error.message}
        requestId={users.error instanceof ApiError ? users.error.requestId : null}
      />
    )
  }
  if (!user) {
    return (
      <ErrorState message="Usuário não encontrado na listagem administrativa disponível." />
    )
  }

  return (
    <UserLayout
      title="Editar usuário"
      description={`${user.email} · ${user.is_active ? 'Ativo' : 'Inativo'}`}
      role={role}
      user={user}
      error={update.error}
    >
      <form
        className="user-form"
        onSubmit={form.handleSubmit((values) => update.mutate(values))}
      >
        <section className="form-section">
          <div className="form-section-heading">
            <h2>Identidade e acesso</h2>
            <p>O e-mail não pode ser alterado pelo contrato atual da API.</p>
          </div>
          <div className="user-form-grid">
            <UserField label="Nome de exibição" error={form.formState.errors.display_name?.message}>
              <input {...form.register('display_name')} />
            </UserField>
            <UserField label="E-mail">
              <input value={user.email} readOnly aria-readonly="true" />
            </UserField>
            <UserField label="Papel">
              <select {...form.register('role')}>
                <option value="admin">Administrador</option>
                <option value="curator">Curador</option>
                <option value="reviewer">Revisor</option>
                <option value="student">Estudante</option>
              </select>
            </UserField>
          </div>
          <label className="active-switch">
            <input type="checkbox" {...form.register('is_active')} />
            <span>
              <strong>Usuário ativo</strong>
              <small>Usuários inativos não podem autenticar.</small>
            </span>
          </label>
        </section>
        <UserActions pending={update.isPending} label="Salvar alterações" />
      </form>
      <PasswordReset userId={userId} />
    </UserLayout>
  )
}

function UserLayout({
  title,
  description,
  role,
  user,
  error,
  children,
}: {
  title: string
  description: string
  role: UserRole
  user?: User
  error: Error | null
  children: React.ReactNode
}) {
  return (
    <div className="user-editor-page">
      <Link className="back-link" to="/users">
        <ArrowLeft size={16} />
        Voltar para usuários
      </Link>
      <PageHeader
        eyebrow="Controle de acesso"
        title={title}
        description={description}
      />
      {error && <InlineError error={error} />}
      <div className="user-editor-layout">
        <main>{children}</main>
        <aside className="user-audit-card">
          <ShieldCheck size={22} />
          <div>
            <p className="eyebrow">Resumo de permissões</p>
            <h2>{roleLabel(role)}</h2>
            <ul>
              {rolePermissions[role].map((permission) => (
                <li key={permission}>{permission}</li>
              ))}
            </ul>
          </div>
          {user && (
            <dl>
              <div><dt>User ID</dt><dd><code>{user.user_id}</code></dd></div>
              <div><dt>Status</dt><dd><StatusBadge value={user.is_active ? 'active' : 'inactive'} /></dd></div>
              <div><dt>Criado em</dt><dd>{formatDate(user.created_at)}</dd></div>
              <div><dt>Atualizado em</dt><dd>{formatDate(user.updated_at)}</dd></div>
              <div><dt>Último login</dt><dd>{formatDate(user.last_login_at)}</dd></div>
            </dl>
          )}
        </aside>
      </div>
    </div>
  )
}

function PasswordReset({ userId }: { userId: string }) {
  const { token } = useAuth()
  const [message, setMessage] = useState('')
  const form = useForm<{ password: string; confirmation: string }>({
    defaultValues: { password: '', confirmation: '' },
  })
  const mutation = useMutation({
    mutationFn: (password: string) =>
      apiRequest<User>(
        `/admin/users/${userId}/reset-password`,
        { method: 'POST', body: JSON.stringify({ password }) },
        token,
      ),
    onSuccess: () => {
      form.reset()
      setMessage('Senha redefinida com sucesso.')
    },
  })
  const password = useWatch({ control: form.control, name: 'password' })

  return (
    <form
      className="password-reset-panel"
      onSubmit={form.handleSubmit((values) => {
        setMessage('')
        if (values.password.length < 12) {
          form.setError('password', { message: 'Use pelo menos 12 caracteres.' })
          return
        }
        if (values.password !== values.confirmation) {
          form.setError('confirmation', { message: 'As senhas não conferem.' })
          return
        }
        mutation.mutate(values.password)
      })}
    >
      <div className="form-section-heading">
        <KeyRound size={20} />
        <div>
          <h2>Redefinir senha</h2>
          <p>A alteração pode revogar sessões existentes desse usuário.</p>
        </div>
      </div>
      {mutation.error && <InlineError error={mutation.error} />}
      {message && <div className="success-alert">{message}</div>}
      <div className="user-form-grid two-columns">
        <UserField label="Nova senha" error={form.formState.errors.password?.message}>
          <input type="password" autoComplete="new-password" {...form.register('password')} />
        </UserField>
        <UserField label="Confirmar nova senha" error={form.formState.errors.confirmation?.message}>
          <input type="password" autoComplete="new-password" {...form.register('confirmation')} />
        </UserField>
      </div>
      <button
        className="button button-secondary"
        disabled={mutation.isPending || password.length < 12}
      >
        <KeyRound size={16} />
        {mutation.isPending ? 'Redefinindo…' : 'Redefinir senha'}
      </button>
    </form>
  )
}

function UserField({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <label className="form-field">
      <span className="field-heading"><strong>{label}</strong></span>
      {children}
      {error && <small className="field-error">{error}</small>}
    </label>
  )
}

function UserActions({ pending, label }: { pending: boolean; label: string }) {
  return (
    <footer className="form-actions">
      <Link className="button button-secondary" to="/users">Cancelar</Link>
      <button className="button button-primary" disabled={pending}>
        <Save size={17} />
        {pending ? 'Salvando…' : label}
      </button>
    </footer>
  )
}

function InlineError({ error }: { error: Error }) {
  return (
    <div className="form-alert inline-form-alert" role="alert">
      <strong>Não foi possível concluir a operação.</strong>
      <span>{error.message}</span>
      {error instanceof ApiError && error.requestId && (
        <small>ID da requisição: {error.requestId}</small>
      )}
    </div>
  )
}

function roleLabel(role: UserRole) {
  return {
    admin: 'Administrador',
    curator: 'Curador',
    reviewer: 'Revisor',
    student: 'Estudante',
  }[role]
}
