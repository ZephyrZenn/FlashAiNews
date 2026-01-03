import { NavLink, useLocation } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import {
  Rss,
  LayoutDashboard,
  Globe,
  History,
  Zap,
  Activity,
  Settings,
} from 'lucide-react';

const navItems = [
  {
    to: '/',
    label: '系统概览',
    icon: LayoutDashboard,
    color: 'text-blue-400',
  },
  {
    to: '/sources',
    label: '订阅源管理',
    icon: Globe,
    color: 'text-cyan-400',
  },
  {
    to: '/history',
    label: '历史简报',
    icon: History,
    color: 'text-indigo-400',
  },
];

const aiLabItems = [
  {
    to: '/instant',
    label: '即时实验室',
    icon: Zap,
    color: 'text-amber-400',
  },
  {
    to: '/schedules',
    label: '自动生成器',
    icon: Activity,
    color: 'text-purple-400',
  },
];

export const Layout = ({ children }: PropsWithChildren) => {
  const location = useLocation();
  const activeTab = location.pathname;

  return (
    <div className="h-screen bg-[#02040a] text-slate-200 flex selection:bg-cyan-500/30 font-sans relative overflow-hidden">
      <div className="fixed inset-0 pointer-events-none opacity-20" style={{
        backgroundImage: `linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
        backgroundSize: '40px 40px'
      }}></div>

      <aside className="w-64 border-r border-white/5 h-screen bg-slate-950/80 backdrop-blur-2xl flex flex-col fixed left-0 top-0 z-30">
        <div className="p-6 flex items-center gap-3 cursor-pointer" onClick={() => window.location.href = '/'}>
          <div className="relative p-2 bg-black rounded-xl border border-white/20 shadow-2xl shadow-blue-500/20">
            <Rss size={24} className="text-white" />
          </div>
          <h1 className="text-xl font-black tracking-tighter text-white uppercase italic">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">Flash</span>AiNews
          </h1>
        </div>
        <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.to || (item.to === '/' && activeTab === '/');
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={`flex items-center gap-5 w-full p-4 rounded-2xl transition-all relative group overflow-hidden ${
                  isActive
                    ? 'bg-white text-black shadow-xl shadow-white/5'
                    : 'text-slate-500 hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && <div className="absolute left-0 top-0 w-1 h-full bg-cyan-500"></div>}
                <span className={`${isActive ? 'scale-110 text-black' : 'scale-100 group-hover:scale-110 ' + item.color} transition-transform duration-300 flex-shrink-0`}>
                  <Icon size={20} />
                </span>
                <span className={`text-[11px] font-black tracking-widest uppercase truncate ${isActive ? 'text-black' : ''}`}>{item.label}</span>
              </NavLink>
            );
          })}

          <div className="mt-8 mb-2 px-4 flex items-center gap-2">
            <div className="h-[1px] flex-1 bg-white/10"></div>
            <span className="text-[10px] font-bold text-slate-500 tracking-[0.3em]">AI 实验室</span>
            <div className="h-[1px] flex-1 bg-white/10"></div>
          </div>

          {aiLabItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.to;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={`flex items-center gap-5 w-full p-4 rounded-2xl transition-all relative group overflow-hidden ${
                  isActive
                    ? 'bg-white text-black shadow-xl shadow-white/5'
                    : 'text-slate-500 hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && <div className="absolute left-0 top-0 w-1 h-full bg-cyan-500"></div>}
                <span className={`${isActive ? 'scale-110 text-black' : 'scale-100 group-hover:scale-110 ' + item.color} transition-transform duration-300 flex-shrink-0`}>
                  <Icon size={20} />
                </span>
                <span className={`text-[11px] font-black tracking-widest uppercase truncate ${isActive ? 'text-black' : ''}`}>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
        <div className="p-6 mt-auto border-t border-white/5">
          <NavLink
            to="/settings"
            className={`flex items-center gap-3 w-full p-3 rounded-2xl transition-all border border-transparent ${
              activeTab === '/settings'
                ? 'text-white bg-white/10 border-white/10'
                : 'text-slate-500 hover:text-white'
            }`}
          >
            <Settings size={20} className={activeTab === '/settings' ? '' : 'group-hover:rotate-90 transition-transform duration-700'} />
            <span className="text-xs font-bold tracking-widest uppercase">配置</span>
          </NavLink>
        </div>
      </aside>

      <main className="flex-1 ml-64 h-screen relative z-10 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-white/5 flex-shrink-0 flex items-center justify-between px-10 bg-slate-950/20 backdrop-blur-xl sticky top-0 z-30">
          <div className="flex items-center gap-3 text-slate-400 text-[16px] font-bold tracking-[0.2em] uppercase">
            <div className="w-2 h-2 rounded-full bg-cyan-500 shadow-[0_0_8px_cyan]"></div>
            <span>控制站</span>
            <span className="text-slate-700">→</span>
            <span className="text-white bg-white/5 px-2 py-0.5 rounded border border-white/10 uppercase tracking-tighter">
              {activeTab === '/settings' ? '配置' : activeTab === '/' ? '仪表板' : activeTab === '/sources' ? '订阅源管理' : activeTab === '/history' ? '历史简报' : activeTab === '/instant' ? '即时实验室' : activeTab === '/schedules' ? '自动计划' : activeTab.slice(1)}
            </span>
          </div>
        </header>
        <div className="flex-1 flex flex-col p-6 max-w-6xl mx-auto w-full min-h-0 overflow-hidden relative">
          {children}
        </div>
      </main>
    </div>
  );
};
