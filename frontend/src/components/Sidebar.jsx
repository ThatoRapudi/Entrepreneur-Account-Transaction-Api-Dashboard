import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import logo from '../assets/capitec-logo.png'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '▣' },
  { to: '/accounts', label: 'Accounts', icon: '▤' },
  { to: '/transactions', label: 'Transactions', icon: '⇄' },
  { to: '/loans', label: 'Loans', icon: '◈' },
  { to: '/insurance', label: 'Insurance', icon: '⛨' },
]

/**
 * Dark fixed sidebar, styled after the reference mockup - one nav item
 * per section instead of one long scrolling page. Below ~900px (see
 * styles.css) the label text hides and only the icon shows, so the
 * `title` attribute on each link carries the label as a hover tooltip.
 */
export default function Sidebar() {
  const { logout } = useAuth()

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <img src={logo} alt="Capitec" />
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            title={item.label}
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <button type="button" className="sidebar-logout" onClick={logout}>
        Sign out
      </button>
    </aside>
  )
}
