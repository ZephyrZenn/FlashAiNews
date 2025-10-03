import { NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

const navItems = [
  {
    to: '/',
    label: 'Daily Summary',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M4 4h16v4H4z" />
        <path d="M4 11h10" />
        <path d="M4 16h8" />
        <path d="M4 21h6" />
      </svg>
    ),
  },
  {
    to: '/groups',
    label: 'Groups',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
        <circle cx="7" cy="7" r="3" />
        <circle cx="17" cy="7" r="3" />
        <path d="M4 20a3 3 0 0 1 3-3h0a3 3 0 0 1 3 3" />
        <path d="M14 20a3 3 0 0 1 3-3h0a3 3 0 0 1 3 3" />
      </svg>
    ),
  },
  {
    to: '/feeds',
    label: 'Feeds',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M5 5c8 0 14 6 14 14" />
        <path d="M5 11c4 0 8 4 8 8" />
        <circle cx="6" cy="18" r="2" />
      </svg>
    ),
  },
  {
    to: '/settings',
    label: 'LLM Settings',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" />
        <path d="M19.4 15a1 1 0 0 0 .2 1.09l.1.1a2 2 0 1 1-2.83 2.83l-.1-.1a1 1 0 0 0-1.09-.2 1 1 0 0 0-.6.92V20a2 2 0 0 1-4 0v-.14a1 1 0 0 0-.6-.92 1 1 0 0 0-1.09.2l-.1.1a2 2 0 1 1-2.83-2.83l.1-.1a1 1 0 0 0 .2-1.09 1 1 0 0 0-.92-.6H4a2 2 0 0 1 0-4h.14a1 1 0 0 0 .92-.6 1 1 0 0 0-.2-1.09l-.1-.1a2 2 0 1 1 2.83-2.83l.1.1a1 1 0 0 0 1.09.2h.01a1 1 0 0 0 .59-.92V4a2 2 0 0 1 4 0v.14a1 1 0 0 0 .6.92h.01a1 1 0 0 0 1.09-.2l.1-.1a2 2 0 0 1 2.83 2.83l-.1.1a1 1 0 0 0-.2 1.09v.01a1 1 0 0 0 .92.59H20a2 2 0 0 1 0 4h-.14a1 1 0 0 0-.92.6Z" />
      </svg>
    ),
  },
];

export const Layout = ({ children }: PropsWithChildren) => {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">FN</div>
          <span>FlashNews</span>
        </div>
        <nav className="nav-links">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              end={item.to === '/'}
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-panel">{children}</main>
    </div>
  );
};
