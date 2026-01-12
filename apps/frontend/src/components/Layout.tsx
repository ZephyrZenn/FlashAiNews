import { NavLink, useLocation } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import {
  Rss,
  Calendar,
  Zap,
  AlarmClock,
  LayoutGrid,
  List,
  Settings,
  Plus,
  RefreshCw,
  ArrowLeft,
} from 'lucide-react';

const readViewItems = [
  { to: '/', label: '今日摘要', icon: Calendar },
  { to: '/instant', label: 'AI 实时总结', icon: Zap },
];

const systemItems = [
  { to: '/schedules', label: '定时任务', icon: AlarmClock },
  { to: '/groups', label: '分组管理', icon: LayoutGrid },
  { to: '/sources', label: '所有源', icon: List },
];

interface LayoutProps extends PropsWithChildren {
  onNewClick?: () => void;
  showNewButton?: boolean;
  showBackButton?: boolean;
  onBackClick?: () => void;
}

export const Layout = ({
  children,
  onNewClick,
  showNewButton = false,
  showBackButton = false,
  onBackClick,
}: LayoutProps) => {
  const location = useLocation();
  const activeTab = location.pathname;

  const getPageTitle = () => {
    switch (activeTab) {
      case '/':
        return '摘要看板';
      case '/instant':
        return 'Agent 总结生成';
      case '/groups':
        return '分组管理';
      case '/sources':
        return '订阅源列表';
      case '/schedules':
        return '自动化策略';
      case '/settings':
        return '系统全局设置';
      default:
        return 'FlashAiNews';
    }
  };

  const shouldShowNewButton = ['/groups', '/sources', '/schedules'].includes(activeTab);

  return (
    <div className="h-screen w-full bg-[#FAFBFC] text-slate-700 flex overflow-hidden font-sans selection:bg-indigo-100">
      {/* 侧边栏 */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 shadow-sm">
        <div className="p-8 flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-xl text-white shadow-lg shadow-indigo-200">
            <Rss size={20} />
          </div>
          <h1 className="font-bold text-lg tracking-tight">FlashAiNews</h1>
        </div>

        <nav className="flex-1 px-4 space-y-1 overflow-y-auto custom-scrollbar">
          <div className="px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
            阅读视图
          </div>
          {readViewItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.to;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-600 font-bold'
                    : 'hover:bg-slate-50 text-slate-500'
                }`}
              >
                <Icon size={18} />
                <span className="text-sm">{item.label}</span>
              </NavLink>
            );
          })}

          <div className="h-4" />
          <div className="px-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
            系统管理
          </div>
          {systemItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.to;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-600 font-bold'
                    : 'hover:bg-slate-50 text-slate-500'
                }`}
              >
                <Icon size={18} />
                <span className="text-sm">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="p-6 border-t border-slate-50">
          <NavLink
            to="/settings"
            className={`w-full flex items-center justify-center gap-2 p-3 rounded-2xl transition-all text-xs font-bold ${
              activeTab === '/settings'
                ? 'bg-indigo-50 text-indigo-600'
                : 'bg-slate-50 text-slate-400 hover:text-indigo-600'
            }`}
          >
            <Settings size={16} />
            <span>系统设置</span>
          </NavLink>
        </div>
      </aside>

      {/* 主内容 */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        <header className="h-20 bg-white/80 backdrop-blur-md border-b border-slate-100 flex items-center justify-between px-8 shrink-0 z-20">
          <div className="text-xl font-black text-slate-800 flex items-center gap-3">
            {showBackButton && onBackClick && (
              <button
                onClick={onBackClick}
                className="p-2 hover:bg-slate-50 rounded-full transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
            )}
            {getPageTitle()}
          </div>
          <div className="flex items-center gap-3">
            {shouldShowNewButton && onNewClick && (
              <button
                onClick={onNewClick}
                className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-2xl text-sm font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all"
              >
                <Plus size={18} />
                <span>新建</span>
              </button>
            )}
            <div className="h-8 w-[1px] bg-slate-100 mx-2" />
            <button className="p-2.5 text-slate-300 hover:text-indigo-600 transition-all hover:bg-slate-50 rounded-xl">
              <RefreshCw size={18} />
            </button>
          </div>
        </header>

        <div className="flex-1 relative overflow-hidden bg-[#F8F9FA]">
          {children}
        </div>
      </div>
    </div>
  );
};
