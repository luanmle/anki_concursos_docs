import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowRight, BookOpenText as BookOpenCheck, ShieldCheck } from '@phosphor-icons/react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/auth-context'

const schema = z.object({
  email: z.string().email('Informe um e-mail válido.'),
  password: z.string().min(8, 'A senha deve ter pelo menos 8 caracteres.'),
})

type LoginValues = z.infer<typeof schema>

export function LoginPage() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(schema) })

  // Preserve the originally-requested URL (path + query, e.g. ?note=...) so
  // deep links survive the login redirect.
  const from =
    (location.state as { from?: { pathname?: string; search?: string } } | null)
      ?.from
  const target = from ? `${from.pathname ?? '/'}${from.search ?? ''}` : '/'

  if (user) return <Navigate to={target} replace />

  async function onSubmit(values: LoginValues) {
    setError('')
    try {
      await login(values.email, values.password)
      navigate(target, { replace: true })
    } catch (caught) {
      setError(
        caught instanceof ApiError && caught.status === 0
          ? caught.message
          : 'E-mail ou senha inválidos.',
      )
    }
  }

  return (
    <main className="login-page">
      <section className="login-intro">
        <div className="login-brand">
          <span>AC</span>
          Anki Concursos
        </div>
        <div className="login-copy">
          <p className="eyebrow">Curadoria com rastreabilidade</p>
          <h1>Conteúdo confiável, versões preservadas.</h1>
          <p>
            Revise cartões, publique releases e mantenha cada decisão auditável
            em um único fluxo administrativo.
          </p>
        </div>
        <div className="login-principles">
          <span>
            <ShieldCheck size={20} /> Versões publicadas são imutáveis
          </span>
          <span>
            <BookOpenCheck size={20} /> Revisão humana antes da publicação
          </span>
        </div>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <p className="eyebrow">Acesso interno</p>
            <h2>Entrar no console</h2>
            <p>Use as credenciais administrativas do ambiente.</p>
          </div>
          {error && <div className="form-alert">{error}</div>}
          <label>
            E-mail
            <input
              type="email"
              autoComplete="email"
              placeholder="nome@exemplo.com"
              {...register('email')}
            />
            {errors.email && <small>{errors.email.message}</small>}
          </label>
          <label>
            Senha
            <input
              type="password"
              autoComplete="current-password"
              placeholder="Sua senha"
              {...register('password')}
            />
            {errors.password && <small>{errors.password.message}</small>}
          </label>
          <button className="button button-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Entrando…' : 'Entrar'}
            {!isSubmitting && <ArrowRight size={18} />}
          </button>
          <p className="login-help">
            Não há recuperação automática de senha. Contate um administrador.
          </p>
        </form>
      </section>
    </main>
  )
}
