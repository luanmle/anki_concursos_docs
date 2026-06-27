import {
  Pulse as Activity,
  BookOpenText as BookOpenCheck,
  CaretDown,
  Layout,
  SignOut,
  Plug as PlugZap,
  MagnifyingGlass as Search,
  UsersThree,
} from '@phosphor-icons/react'
import type { CSSProperties } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/auth-context'
import { translateStatus } from '../lib/presentation'
import { Avatar, AvatarFallback } from './ui/avatar'
import { Button } from './ui/button'
import { Separator } from './ui/separator'
import { ThemeToggle } from './ThemeToggle'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
} from './ui/sidebar'

const studentNav = [
  { to: '/', label: 'Explore', icon: Search },
  { to: '/my-decks', label: 'Meus baralhos', icon: BookOpenCheck },
  { to: '/community', label: 'Comunidade', icon: UsersThree },
]

function initials(name?: string) {
  return (name || 'U').slice(0, 2).toUpperCase()
}

function ShellNavLink({
  to,
  label,
  icon: Icon,
  end = false,
}: {
  to: string
  label: string
  icon: typeof Search
  end?: boolean
}) {
  const { setOpenMobile } = useSidebar()

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild className="muriae-sidebar-link">
        <NavLink
          to={to}
          end={end}
          onClick={() => setOpenMobile(false)}
        >
          <Icon size={19} aria-hidden="true" />
          <span>{label}</span>
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}

function AppShellLayout() {
  const { user, logout, hasRole } = useAuth()
  const environment = (
    window.__APP_CONFIG__?.APP_ENV ||
    import.meta.env.VITE_APP_ENV ||
    'STAGING'
  ).toUpperCase()
  const teamNav = [
    ...(hasRole('admin', 'curator', 'reviewer')
      ? [{ to: '/admin', label: 'Administração', icon: Layout }]
      : []),
    { to: '/addon', label: 'Add-on do Anki', icon: PlugZap },
    ...(hasRole('admin')
      ? [{ to: '/operation', label: 'Operação', icon: Activity }]
      : []),
  ]

  return (
    <>
      <Sidebar collapsible="offcanvas" className="muriae-sidebar-container">
        <SidebarHeader className="muriae-sidebar-header">
          <div className="muriae-brand-mark" aria-hidden="true">
            <span />
          </div>
          <div className="muriae-brand-name">
            <strong>Muriae</strong>
            <span>concursos</span>
          </div>
        </SidebarHeader>
        <SidebarContent className="muriae-sidebar-content">
          <SidebarGroup className="muriae-sidebar-group">
            <SidebarGroupContent>
              <SidebarMenu className="muriae-sidebar-menu">
                {studentNav.map((item) => (
                  <ShellNavLink key={item.to} {...item} end={item.to === '/'} />
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
          <SidebarGroup className="muriae-sidebar-group muriae-team-group">
            <SidebarGroupLabel className="muriae-sidebar-label">
              Equipe
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu className="muriae-sidebar-menu">
                {teamNav.map((item) => (
                  <ShellNavLink key={item.to} {...item} />
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter className="muriae-sidebar-footer">
          <Separator className="muriae-sidebar-footer-line" />
          <div className="muriae-sidebar-user-row">
            <Button
              type="button"
              variant="ghost"
              className="muriae-sidebar-user"
              aria-label="Abrir configurações"
            >
              <Avatar className="muriae-avatar">
                <AvatarFallback>{initials(user?.display_name)}</AvatarFallback>
              </Avatar>
              <span className="muriae-user-copy">
                <strong>{user?.display_name}</strong>
                <span>{user && translateStatus(user.role)}</span>
              </span>
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="muriae-sidebar-logout"
              aria-label="Sair"
              onClick={logout}
            >
              <SignOut size={18} />
            </Button>
          </div>
        </SidebarFooter>
      </Sidebar>
      <div className="content-frame muriae-content-frame">
        <header className="topbar">
          <SidebarTrigger className="mobile-menu-button" aria-label="Abrir navegação" />
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
            <ThemeToggle />
            <div>
              <strong>{user?.display_name}</strong>
              <span>{user && translateStatus(user.role)}</span>
            </div>
            <div className="avatar">{initials(user?.display_name)}</div>
            <CaretDown size={15} aria-hidden="true" />
          </div>
        </header>
        <main className="main-content ac-main-content">
          <Outlet />
        </main>
      </div>
    </>
  )
}

export function AppShell() {
  return (
    <SidebarProvider
      className="app-shell"
      style={{
        '--sidebar-width': '264px',
      } as CSSProperties}
    >
      <AppShellLayout />
    </SidebarProvider>
  )
}
