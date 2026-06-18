import {
  Activity,
  BookOpenCheck,
  ChevronDown,
  FileWarning,
  LayoutDashboard,
  Library,
  LogOut,
  Menu,
  PlugZap,
  Search,
  ShieldCheck,
  Users,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/auth-context'
import { translateStatus } from '../lib/presentation'

const studentNav = [
  { to: '/', label: 'Explore', icon: Search },
  { to: '/my-decks', label: 'Meus Baralhos', icon: BookOpenCheck },
  { to: '/community', label: 'Community', icon: PlugZap },
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
    ...studentNav,
    ...(hasRole('admin', 'curator', 'reviewer')
      ? [{ to: '/admin', label: 'Administracao', icon: LayoutDashboard }]
      : []),
    ...(hasRole('admin', 'curator')
      ? [{ to: '/admin/decks', label: 'Gerenciar Baralhos', icon: Library }]
      : []),
    ...(hasRole('admin', 'reviewer')
      ? [{ to: '/admin/suggestions', label: 'Sugestoes', icon: FileWarning }]
      : []),
    ...(hasRole('admin', 'curator')
      ? [{ to: '/cards', label: 'Cartoes internos', icon: Library }]
      : []),
    ...(hasRole('admin', 'curator')
      ? [{ to: '/decks', label: 'Decks internos', icon: BookOpenCheck }]
      : []),
    ...(hasRole('admin', 'reviewer')
      ? [{ to: '/reports', label: 'Reports', icon: FileWarning }]
      : []),
    ...(hasRole('admin')
      ? [{ to: '/users', label: 'Usuarios', icon: Users }]
      : []),
    { to: '/addon', label: 'Add-on', icon: PlugZap },
    { to: '/operation', label: 'Operacao', icon: Activity },
  ]

  return (
    <div className="app-shell ac-shell">
      <button
        className="mobile-menu-button"
        type="button"
        aria-label="Abrir navegacao"
        onClick={() => setOpen(true)}
      >
        <Menu size={22} />
      </button>
      {open && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Fechar navegacao"
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
            <span>Web Interface</span>
          </div>
          <button
            className="sidebar-close"
            type="button"
            aria-label="Fechar navegacao"
            onClick={() => setOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        <nav className="sidebar-nav" aria-label="Navegacao principal">
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
        <main className="main-content ac-main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
