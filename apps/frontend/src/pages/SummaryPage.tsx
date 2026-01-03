import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Zap,
} from 'lucide-react';

const SummaryPage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex-1 flex flex-col items-center justify-center py-10 text-center animate-in fade-in slide-in-from-top-10 duration-1000">
      <div className="relative mb-12 group cursor-pointer" onClick={() => navigate('/instant')}>
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-purple-600 blur-[60px] opacity-20 group-hover:opacity-40 transition-all duration-1000"></div>
        <div className="relative p-12 bg-slate-900/40 border border-white/10 rounded-[4rem] backdrop-blur-3xl shadow-2xl">
          <LayoutDashboard size={80} className="text-white group-hover:scale-110 transition-transform duration-500" />
        </div>
      </div>
      <h2 className="text-5xl font-black text-white mb-4 tracking-tighter italic uppercase leading-none">
        Flash Ai News
      </h2>
      <p className="text-slate-500 max-w-lg mb-10 leading-relaxed font-light text-lg italic tracking-tight">
        欢迎来到 FlashAiNews 控制站
      </p>
      <button
        onClick={() => navigate('/instant')}
        className="px-10 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-black rounded-full shadow-[0_0_40px_rgba(6,182,212,0.3)] flex items-center gap-3 hover:scale-105 transition-all text-xs uppercase tracking-widest mx-auto"
      >
        启动手动核心 <Zap size={18} className="fill-current" />
      </button>
    </div>
  );
};

export default SummaryPage;

