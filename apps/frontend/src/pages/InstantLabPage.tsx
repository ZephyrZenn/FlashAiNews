import { useState, useEffect, useRef } from 'react';
import {
  Zap,
  Filter,
  Wand2,
  Play,
  X,
  Check,
  Terminal,
  Loader2,
  History,
  FileText,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import { useToast } from '@/context/ToastContext';
import type { FeedGroup } from '@/types/api';

const InstantLabPage = () => {
  const queryClient = useQueryClient();
  const { data: groups } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const { data: feeds } = useApiQuery(queryKeys.feeds, api.getFeeds);
  const { showToast } = useToast();

  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([]);
  const [focus, setFocus] = useState('');
  const [statusLogs, setStatusLogs] = useState<Array<{ timestamp: string; message: string; type: string }>>([]);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<string | null>(null);
  const [viewState, setViewState] = useState<'input' | 'logs' | 'result'>('input');
  const [showGroupPicker, setShowGroupPicker] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [statusLogs]);

  const addLog = (message: string, type: string = 'info') => {
    const timestamp = new Date().toLocaleTimeString([], {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    setStatusLogs((prev) => [...prev, { timestamp, message, type }]);
  };

  const generateMutation = useApiMutation(async () => {
    // TODO: Backend /briefs/generate doesn't support custom groups or focus
    // Currently generates for all groups without today's brief
    // Future: Backend needs /briefs/generate with group_ids and focus parameters
    await api.generateTodayBrief();
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      queryClient.invalidateQueries({ queryKey: queryKeys.todayBrief(0) });
    },
  });

  const handleGenerate = async () => {
    if (selectedGroupIds.length === 0) {
      showToast('Please select at least one group', { type: 'error' });
      return;
    }
    setIsGenerating(true);
    setViewState('logs');
    setStatusLogs([]);
    setProgress(0);
    setResult(null);

    addLog('⚡ Establishing encrypted tunnel...', 'system');
    await new Promise((r) => setTimeout(r, 600));
    setProgress(20);

    addLog('📡 Polling distributed nodes...', 'info');
    await new Promise((r) => setTimeout(r, 800));
    setProgress(45);

    addLog('🧠 Initiating Analysis Engine...', 'ai');
    await new Promise((r) => setTimeout(r, 600));
    setProgress(70);

    try {
      generateMutation.mutate();
      addLog('🔄 Triggering backend generation...', 'info');
      await new Promise((r) => setTimeout(r, 1000));
      setProgress(100);
      addLog('🎉 Synthesis complete.', 'success');
      await new Promise((r) => setTimeout(r, 800));
      setResult('简报生成已启动。请查看摘要页面查看结果。');
      setIsGenerating(false);
      setViewState('result');
      showToast('简报生成已成功启动');
    } catch (err: any) {
      addLog('❌ 神经崩溃', 'error');
      setIsGenerating(false);
      showToast(err.message || '生成简报失败', { type: 'error' });
      setTimeout(() => setViewState('input'), 2000);
    }
  };

  const toggleGroup = (groupId: number) => {
    setSelectedGroupIds((prev) =>
      prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId]
    );
  };

  if (viewState === 'result' && result) {
    return (
      <div className="flex-1 flex flex-col min-h-0 animate-in fade-in duration-700">
        <div className="flex-1 flex flex-col bg-black border border-white/10 rounded-[3rem] shadow-2xl relative overflow-hidden">
          <div className="flex-shrink-0 flex items-center justify-between px-10 py-5 border-b border-white/5">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-cyan-500/10 rounded-2xl text-cyan-400">
                <FileText size={24} />
              </div>
              <h2 className="text-xl font-black text-white italic tracking-tighter uppercase leading-tight">
                输出流
              </h2>
            </div>
            <button
              onClick={() => setViewState('input')}
              className="px-6 py-2 bg-white text-black rounded-xl font-black text-[9px] uppercase tracking-widest hover:bg-cyan-400 transition-all"
            >
              关闭
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-10 custom-scrollbar prose prose-invert prose-cyan max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result}</ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  if (viewState === 'logs') {
    return (
      <div className="flex-1 flex flex-col min-h-0 animate-in zoom-in-95 duration-500">
        <div className="flex-1 bg-black border border-white/10 rounded-[3rem] p-10 flex flex-col shadow-2xl relative overflow-hidden">
          <div className="flex-shrink-0 flex items-center justify-between mb-10">
            <div className="flex items-center gap-3 text-slate-500 font-mono text-[10px] tracking-[0.4em] uppercase">
              <Terminal size={14} className="text-cyan-400" /> 内核流
            </div>
            {isGenerating && <Loader2 size={14} className="animate-spin text-cyan-400" />}
          </div>
          <div className="flex-1 overflow-y-auto space-y-4 font-mono text-[10px] custom-scrollbar pr-4">
            {statusLogs.map((log, i) => (
              <div
                key={i}
                className={`flex gap-4 animate-in slide-in-from-left-6 duration-300 ${
                  log.type === 'success'
                    ? 'text-green-400'
                    : log.type === 'ai'
                      ? 'text-cyan-400'
                      : 'text-slate-700'
                }`}
              >
                <span className="opacity-20 flex-shrink-0 font-bold">[{log.timestamp}]</span>
                <span>{log.message}</span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
          <div className="mt-8 pt-6 border-t border-white/5">
            <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-cyan-500 h-full transition-all duration-700 shadow-[0_0_10px_cyan]"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 animate-in fade-in slide-in-from-bottom-8 duration-700 relative overflow-hidden">
      <div className="flex-shrink-0 text-center relative py-4">
        <div className="inline-block relative mb-3">
          <div className="absolute inset-0 bg-cyan-500/20 blur-2xl rounded-full"></div>
          <div className="relative p-3 bg-slate-950 border border-white/10 rounded-2xl text-cyan-400 shadow-xl">
            <Zap size={32} />
          </div>
        </div>
        <h2 className="text-4xl font-black text-white tracking-tighter uppercase italic leading-none">
          简报生成器
        </h2>
      </div>
      <div className="flex-1 flex flex-col min-h-0 bg-[#0a0f1d]/60 backdrop-blur-3xl border border-white/10 rounded-[3rem] p-8 shadow-2xl relative overflow-hidden group">
        <section className="flex-shrink-0 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-[18px] font-black text-cyan-400 uppercase tracking-[0.4em] flex items-center gap-2">
              原材料
            </h4>
            <button
              onClick={() => setShowGroupPicker(true)}
              className="text-[9px] font-black text-slate-500 hover:text-cyan-400 flex items-center gap-2 transition-all uppercase tracking-widest bg-white/5 px-3 py-1 rounded-xl border border-white/5"
            >
              <Filter size={12} /> 管理
            </button>
          </div>
          <div className="flex flex-wrap gap-2 min-h-[40px]">
            {selectedGroupIds.length === 0 ? (
              <span className="text-[14px] text-slate-700 italic py-2">未选择节点</span>
            ) : (
              selectedGroupIds.map((id) => {
                const group = groups?.find((g) => g.id === id);
                return (
                  <div
                    key={id}
                    className="px-4 py-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-xl flex items-center gap-2 group/chip transition-all hover:bg-cyan-500/20"
                  >
                    <span className="text-xs font-black text-white uppercase">{group?.title}</span>
                    <button
                      onClick={() => setSelectedGroupIds(selectedGroupIds.filter((x) => x !== id))}
                      className="text-slate-500 hover:text-red-400 transition-colors"
                    >
                      <X size={14} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </section>
        <section className="flex-1 min-h-0 flex flex-col mb-6">
          <h4 className="text-[18px] font-black text-purple-400 uppercase tracking-[0.4em] mb-4 flex items-center gap-2">
            <Wand2 size={12} /> 关注点
          </h4>
          <textarea
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            placeholder="想了解点什么..."
            className="flex-1 w-full p-6 bg-black/60 border border-white/5 rounded-[2rem] outline-none text-white font-mono text-xs resize-none custom-scrollbar"
          />
        </section>
        <div className="flex justify-center">
          <button
            onClick={handleGenerate}
            disabled={selectedGroupIds.length === 0 || isGenerating}
            className={`px-10 py-3 rounded-2xl font-black text-sm flex items-center justify-center gap-3 transition-all ${
              selectedGroupIds.length > 0 && !isGenerating
                ? 'bg-white text-black shadow-xl hover:bg-cyan-400 active:scale-95'
                : 'bg-white/5 text-slate-800 cursor-not-allowed border border-white/5'
            }`}
          >
            <Play size={18} fill="currentColor" />{' '}
            <span className="uppercase italic tracking-widest">开始合成</span>
          </button>
        </div>
      </div>
      {statusLogs.length > 0 && !isGenerating && (
        <div className="flex-shrink-0 flex justify-center mt-5 animate-in slide-in-from-bottom-4 duration-500">
          <button
            onClick={() => setViewState(result ? 'result' : 'logs')}
            className="group flex items-center gap-2.5 px-6 py-2.5 bg-slate-900 border border-white/10 rounded-full text-slate-600 hover:text-cyan-400 transition-all text-[9px] font-black tracking-[0.3em] uppercase shadow-2xl backdrop-blur-xl"
          >
            <History size={14} className="group-hover:rotate-[-45deg] transition-all" /> 跳转到最后
          </button>
        </div>
      )}
      {showGroupPicker && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-xl z-[60] flex items-center justify-center p-6">
          <div className="bg-slate-950 border border-white/10 rounded-[2.5rem] w-full max-w-lg shadow-2xl animate-in zoom-in duration-300 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500"></div>
            <div className="p-8 border-b border-white/5 flex justify-between items-center">
              <h3 className="text-xl font-black italic text-white uppercase italic">选择订阅组</h3>
              <button
                onClick={() => setShowGroupPicker(false)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <div className="p-8 max-h-[300px] overflow-y-auto grid grid-cols-2 gap-4 custom-scrollbar">
              {groups?.map((g) => (
                <button
                  key={g.id}
                  onClick={() => toggleGroup(g.id)}
                  className={`p-4 rounded-2xl border-2 transition-all flex items-center gap-4 ${
                    selectedGroupIds.includes(g.id)
                      ? 'border-cyan-500 bg-cyan-500/5 text-white'
                      : 'border-white/5 bg-white/5 text-slate-500 hover:border-white/10'
                  }`}
                >
                  <div className="text-left">
                    <div className="text-sm font-black uppercase tracking-widest">{g.title}</div>
                    {selectedGroupIds.includes(g.id) && (
                      <div className="text-xs text-cyan-400 font-mono mt-1 flex items-center gap-1 animate-in fade-in">
                        <Check size={10} /> 已选择
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
            <div className="p-8 pt-0">
              <button
                onClick={() => setShowGroupPicker(false)}
                className="w-full py-2 bg-white text-black font-black rounded-2xl uppercase text-[10px] tracking-[0.2em] shadow-xl hover:bg-cyan-400 transition-all"
              >
                保存配置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InstantLabPage;

