import { useState, useRef, useEffect } from 'react';
import {
  Zap,
  PlayCircle,
  RotateCcw,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { Layout } from '@/components/Layout';
import { useToast } from '@/context/ToastContext';
import { useTaskPolling } from '@/hooks/useTaskPolling';
import type { FeedGroup } from '@/types/api';

interface LogEntry {
  text: string;
  time: string;
}

const InstantLabPage = () => {
  const queryClient = useQueryClient();
  const { data: groups } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const { showToast } = useToast();

  const [taskId, setTaskId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [agentLogs, setAgentLogs] = useState<LogEntry[]>([]);
  const [generationFocus, setGenerationFocus] = useState('');
  const [selectedGroupsForGen, setSelectedGroupsForGen] = useState<number[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  const allGroups = groups ?? [];

  // 自动滚动到底部
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [agentLogs]);

  // 使用轮询 hook 获取任务状态
  useTaskPolling({
    taskId,
    enabled: !!taskId && isGenerating,
    interval: 10000, // 每秒轮询一次
    onLogUpdate: (logs) => {
      setAgentLogs(
        logs.map(log => ({
          text: log.text,
          time: new Date(log.time).toLocaleTimeString(),
        }))
      );
    },
    onComplete: () => {
      setIsGenerating(false);
      setTaskId(null);
      showToast('简报生成成功！');
      queryClient.invalidateQueries({ queryKey: queryKeys.briefs() });
      queryClient.invalidateQueries({ queryKey: queryKeys.defaultBriefs });
    },
    onError: (error) => {
      setIsGenerating(false);
      setTaskId(null);
      showToast(`生成失败: ${error}`, { type: 'error' });
    },
  });

  const startGeneration = async () => {
    if (selectedGroupsForGen.length === 0) return;
    
    try {
      setIsGenerating(true);
      setAgentLogs([]);
      
      // 创建brief生成任务并获取任务ID
      const { task_id } = await api.generateBrief(
        selectedGroupsForGen,
        generationFocus
      );
      
      setTaskId(task_id);
    } catch (error) {
      setIsGenerating(false);
      showToast('启动任务失败', { type: 'error' });
    }
  };

  const resetGeneration = () => {
    setIsGenerating(false);
    setAgentLogs([]);
    setTaskId(null);
    setGenerationFocus('');
    setSelectedGroupsForGen([]);
  };

  const toggleGroupForGen = (groupId: number) => {
    setSelectedGroupsForGen((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    );
  };

  // Console view - when generating or has logs
  if (isGenerating || agentLogs.length > 0) {
    return (
      <Layout>
        <div className="h-full overflow-hidden p-12 flex flex-col items-center">
          <div className="w-full max-w-4xl flex flex-col h-full animate-in zoom-in-95 duration-300">
            {/* Console header */}
            <div className="bg-slate-900 rounded-t-[3rem] p-8 text-white flex items-center justify-between shadow-2xl border-b border-white/5">
              <div className="flex items-center gap-4">
                <div
                  className={`w-3 h-3 rounded-full ${
                    isGenerating
                      ? 'bg-amber-400 animate-pulse'
                      : 'bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.5)]'
                  }`}
                />
                <div className="font-mono text-sm tracking-widest font-black uppercase">
                  Agent Logic Console
                </div>
              </div>
              {!isGenerating && (
                <button
                  onClick={resetGeneration}
                  className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-xl text-xs font-bold border border-white/10 transition-all"
                >
                  <RotateCcw size={14} /> 开启新总结
                </button>
              )}
            </div>

            {/* Console body */}
            <div className="flex-1 bg-slate-900 rounded-b-[3rem] p-8 font-mono text-sm overflow-hidden flex flex-col shadow-2xl">
              <div className="flex-1 overflow-y-auto custom-scrollbar-terminal pr-4 space-y-4">
                {agentLogs.map((log, i) => (
                  <div
                    key={i}
                    className="flex gap-4 animate-in fade-in duration-700"
                  >
                    <span className="text-indigo-500/60 shrink-0">
                      [{log.time}]
                    </span>
                    <span
                      className={
                        i === agentLogs.length - 1
                          ? 'text-indigo-300 font-bold border-l-2 border-indigo-500 pl-3 ml-2'
                          : 'text-slate-400 ml-3 pl-3 border-l border-white/5'
                      }
                    >
                      {log.text}
                    </span>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  // Input form view - exactly matching t.tsx generate tab
  return (
    <Layout>
      <div className="h-full overflow-hidden p-12 flex flex-col items-center">
        <div className="w-full max-w-2xl bg-white rounded-[3rem] border border-slate-100 p-10 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Header */}
          <div className="mb-10 flex items-center gap-4">
            <div className="w-14 h-14 bg-indigo-600 rounded-[1.5rem] flex items-center justify-center text-white shadow-lg shadow-indigo-100">
              <Zap size={28} />
            </div>
            <div>
              <h3 className="text-2xl font-black text-slate-800">
                实时 Agent 总结
              </h3>
              <p className="text-slate-400 text-sm font-medium">
                配置偏好并启动即时分析
              </p>
            </div>
          </div>

          <div className="space-y-8">
            {/* Focus input */}
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 ml-2">
                用户关注点 (可选)
              </label>
              <textarea
                value={generationFocus}
                onChange={(e) => setGenerationFocus(e.target.value)}
                placeholder="例如：关注 AI 在移动端的应用..."
                className="w-full bg-slate-50 border-none rounded-[2rem] px-6 py-5 text-sm focus:ring-2 focus:ring-indigo-500/20 resize-none outline-none h-32"
              />
            </div>

            {/* Group selection */}
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 ml-2">
                目标分组
              </label>
              <div className="flex flex-wrap gap-2 px-1">
                {allGroups.map((group) => (
                  <button
                    key={group.id}
                    onClick={() => toggleGroupForGen(group.id)}
                    className={`px-5 py-3 rounded-2xl text-xs font-bold transition-all border ${
                      selectedGroupsForGen.includes(group.id)
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-100'
                        : 'bg-white text-slate-500 border-slate-200 hover:border-indigo-200'
                    }`}
                  >
                    {group.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate button */}
            <button
              onClick={startGeneration}
              disabled={selectedGroupsForGen.length === 0}
              className="w-full py-5 bg-indigo-600 text-white rounded-[2rem] font-black shadow-xl shadow-indigo-100 hover:bg-indigo-700 disabled:opacity-40 transition-all flex items-center justify-center gap-3 text-lg mt-4"
            >
              <PlayCircle size={24} />
              启动总结任务
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default InstantLabPage;
