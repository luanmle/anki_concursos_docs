import {
  Activity,
  BookOpenCheck,
  FileWarning,
  Library,
  LayoutDashboard,
  LogOut,
  Menu,
  Users,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/auth-context'
import { translateStatus } from '../lib/presentation'

const baseNav = [
  { to: '/', label: 'Visão geral', icon: LayoutDashboard },
  { to: '/cards', label: 'Cartões', icon: Library },
  { to: '/decks', label: 'Decks', icon: BookOpenCheck },
  { to: '/reports', label: 'Reports', icon: FileWarning },
  { to: '/operation', label: 'Operação', icon: Activity },
]

export function AppShell() {
  const { user, logout, hasRole } = useAuth()
  const [open, setOpen] = useState(false)
  const nav = hasRole('admin')
    ? [...baseNav.slice(0, 4), { to: '/users', label: 'Usuários', icon: Users }, baseNav[4]]
    : baseNav

  return (
    <div className="app-shell">
      <button
        className="mobile-menu-button"
        type="button"
        aria-label="Abrir navegação"
        onClick={() => setOpen(true)}
      >
        <Menu size={22} />
      </button>
      {open && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Fechar navegação"
          onClick={() => setOpen(false)}
        />
      )}
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">AC</div>
          <div>
            <strong>Anki Concursos</strong>
            <span>Console administrativo</span>
          </div>
          <button
            className="sidebar-close"
            type="button"
            aria-label="Fechar navegação"
            onClick={() => setOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        <span className="environment-badge">
          {window.__APP_CONFIG__?.APP_ENV ||
            import.meta.env.VITE_APP_ENV ||
            'STAGING'}
        </span>
        <nav className="sidebar-nav" aria-label="Navegação principal">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
            >
              <Icon size={19} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-user">
          <div className="avatar">{user?.display_name.slice(0, 2).toUpperCase()}</div>
          <div>
            <strong>{user?.display_name}</strong>
            <span>{user && translateStatus(user.role)}</span>
          </div>
          <button type="button" aria-label="Sair" onClick={logout}>
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
