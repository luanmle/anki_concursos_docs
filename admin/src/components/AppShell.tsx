import {
  Activity,
  BookOpenCheck,
  ChevronDown,
  FileWarning,
  Library,
  LayoutDashboard,
  LogOut,
  Menu,
  PlugZap,
  ShieldCheck,
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
  { to: '/addon', label: 'Add-on', icon: PlugZap },
  { to: '/operation', label: 'Operação', icon: Activity },
]

export function AppShell() {
  const { user, logout, hasRole } = useAuth()
  const [open, setOpen] = useState(false)
  const environment = (
    window.__APP_CONFIG__?.APP_ENV ||
    import.meta.env.VITE_APP_ENV ||
    'STAGING'
  ).toUpperCase()
  const nav = [
    ...baseNav.slice(0, 4),
    ...(hasRole('admin', 'reviewer')
      ? [{ to: '/reports', label: 'Reports', icon: FileWarning }]
      : []),
    ...(hasRole('admin')
      ? [{ to: '/users', label: 'Usuários', icon: Users }]
      : []),
    baseNav[4],
  ]

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
          <div className="brand-mark">
            <ShieldCheck size={19} />
          </div>
          <div>
            <strong>Anki Concursos</strong>
            <span>Admin Console</span>
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
      <div className="content-frame">
        <header className="topbar">
          <div className="topbar-context">
            <span className={`environment-badge environment-${environment.toLowerCase()}`}>
              {environment}
            </span>
            <span className="connection-indicator">
              <i />
              API conectada
            </span>
          </div>
          <div className="topbar-user">
            <div>
              <strong>{user?.display_name}</strong>
              <span>{user && translateStatus(user.role)}</span>
            </div>
            <div className="avatar">{user?.display_name.slice(0, 2).toUpperCase()}</div>
            <ChevronDown size={15} aria-hidden="true" />
          </div>
        </header>
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
