import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Zap,
  PlayCircle,
  RotateCcw,
  Info,
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

const TASK_STORAGE_KEY = 'instant_lab_active_task';

const InstantLabPage = () => {
  const queryClient = useQueryClient();
  const { data: groups } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const { showToast } = useToast();

  const [taskId, setTaskId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [agentLogs, setAgentLogs] = useState<LogEntry[]>([]);
  const [generationFocus, setGenerationFocus] = useState('');
  const [selectedGroupsForGen, setSelectedGroupsForGen] = useState<number[]>([]);
  const [boostMode, setBoostMode] = useState(false);
  const [isRecovering, setIsRecovering] = useState(true); // 标记是否正在恢复状态
  const logEndRef = useRef<HTMLDivElement>(null);

  const allGroups = groups ?? [];

  // 组件挂载时检查是否有正在运行的任务
  useEffect(() => {
    const recoverTask = async () => {
      const savedTaskId = localStorage.getItem(TASK_STORAGE_KEY);
      if (savedTaskId) {
        try {
          // 从后端获取任务状态
          const status = await api.getBriefGenerationStatus(savedTaskId);
          if (status.status === 'pending' || status.status === 'running') {
            // 任务仍在运行，恢复状态
            setTaskId(savedTaskId);
            setIsGenerating(true);
            // 恢复已有的日志
            if (status.logs.length > 0) {
              setAgentLogs(
                status.logs.map(log => ({
                  text: log.text,
                  time: new Date(log.time).toLocaleTimeString(),
                }))
              );
            }
          } else {
            // 任务已完成或失败，清除存储
            localStorage.removeItem(TASK_STORAGE_KEY);
          }
        } catch {
          // 任务不存在或出错，清除存储
          localStorage.removeItem(TASK_STORAGE_KEY);
        }
      }
      setIsRecovering(false);
    };

    recoverTask();
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [agentLogs]);

  // 任务完成时的处理
  const handleTaskComplete = useCallback(() => {
    setIsGenerating(false);
    setTaskId(null);
    localStorage.removeItem(TASK_STORAGE_KEY);
    showToast('简报生成成功！');
    queryClient.invalidateQueries({ queryKey: queryKeys.briefs() });
    queryClient.invalidateQueries({ queryKey: queryKeys.defaultBriefs });
  }, [showToast, queryClient]);

  // 任务失败时的处理
  const handleTaskError = useCallback((error: string) => {
    setIsGenerating(false);
    setTaskId(null);
    localStorage.removeItem(TASK_STORAGE_KEY);
    showToast(`生成失败: ${error}`, { type: 'error' });
  }, [showToast]);

  // 日志更新处理
  const handleLogUpdate = useCallback((logs: Array<{ text: string; time: string }>) => {
    setAgentLogs(
      logs.map(log => ({
        text: log.text,
        time: new Date(log.time).toLocaleTimeString(),
      }))
    );
  }, []);

  // 使用轮询 hook 获取任务状态
  useTaskPolling({
    taskId,
    enabled: !!taskId && isGenerating && !isRecovering,
    interval: 3000, // 每3秒轮询一次
    onLogUpdate: handleLogUpdate,
    onComplete: handleTaskComplete,
    onError: handleTaskError,
  });

  const startGeneration = async () => {
    // BoostMode 需要填写 focus，原模式需要至少选择一个分组
    if (boostMode && !generationFocus.trim()) {
      showToast('Boost Mode 下必须填写用户关注点', { type: 'error' });
      return;
    }
    if (!boostMode && selectedGroupsForGen.length === 0) return;
    
    try {
      setIsGenerating(true);
      setAgentLogs([]);
      
      // 创建brief生成任务并获取任务ID
      // BoostMode 时传递空数组，后端会忽略 group_ids
      const { task_id } = await api.generateBrief(
        boostMode ? [] : selectedGroupsForGen,
        generationFocus.trim(),
        boostMode
      );
      
      // 保存到 localStorage，以便页面切换后恢复
      localStorage.setItem(TASK_STORAGE_KEY, task_id);
      setTaskId(task_id);
    } catch (error: any) {
      setIsGenerating(false);
      // FastAPI 返回的错误格式是 { detail: "error message" }
      const errorMessage = error?.response?.data?.detail || error?.message || '启动任务失败';
      showToast(errorMessage, { type: 'error' });
    }
  };

  const resetGeneration = () => {
    setIsGenerating(false);
    setAgentLogs([]);
    setTaskId(null);
    setGenerationFocus('');
    setSelectedGroupsForGen([]);
    setBoostMode(false);
    localStorage.removeItem(TASK_STORAGE_KEY);
  };

  const toggleGroupForGen = (groupId: number) => {
    setSelectedGroupsForGen((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    );
  };

  // 恢复状态时显示加载
  if (isRecovering) {
    return (
      <Layout>
        <div className="h-full overflow-hidden p-4 md:p-12 flex flex-col items-center justify-center">
          <div className="text-slate-400 text-sm">检查任务状态...</div>
        </div>
      </Layout>
    );
  }

  // Console view - when generating or has logs
  if (isGenerating || agentLogs.length > 0) {
    return (
      <Layout>
        <div className="h-full overflow-hidden p-4 md:p-12 flex flex-col items-center">
          <div className="w-full max-w-4xl flex flex-col h-full animate-in zoom-in-95 duration-300">
            {/* Console header */}
            <div className="bg-slate-900 rounded-t-2xl md:rounded-t-[3rem] p-4 md:p-8 text-white flex items-center justify-between shadow-2xl border-b border-white/5">
              <div className="flex items-center gap-4">
                <div
                  className={`w-3 h-3 rounded-full ${
                    isGenerating
                      ? 'bg-amber-400 animate-pulse'
                      : 'bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.5)]'
                  }`}
                />
                <div className="font-mono text-xs md:text-sm tracking-widest font-black uppercase">
                  Agent Logic Console
                </div>
              </div>
              {!isGenerating && (
                <button
                  onClick={resetGeneration}
                  className="flex items-center gap-1 md:gap-2 bg-white/10 hover:bg-white/20 px-3 md:px-4 py-2 rounded-xl text-[10px] md:text-xs font-bold border border-white/10 transition-all min-h-[44px]"
                >
                  <RotateCcw size={14} /> <span className="hidden sm:inline">开启新总结</span>
                </button>
              )}
            </div>

            {/* Console body */}
            <div className="flex-1 bg-slate-900 rounded-b-2xl md:rounded-b-[3rem] p-4 md:p-8 font-mono text-xs md:text-sm overflow-hidden flex flex-col shadow-2xl">
              <div className="flex-1 overflow-y-auto custom-scrollbar-terminal pr-2 md:pr-4 space-y-3 md:space-y-4">
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

  // Input form view - GPT chat-like layout
  return (
    <Layout>
      <div className="h-full overflow-hidden flex flex-col">
        <div className="flex-1 flex flex-col items-center justify-center p-4 md:p-8">
          <div className="w-full max-w-3xl flex flex-col h-full max-h-[800px]">
            {/* Header */}
            <div className="mb-6 md:mb-8 flex items-center gap-3 md:gap-4">
              <div className="w-10 h-10 md:w-12 md:h-12 bg-indigo-600 rounded-xl md:rounded-2xl flex items-center justify-center text-white shadow-lg shadow-indigo-100">
                <Zap size={20} className="md:w-6 md:h-6" />
              </div>
              <div>
                <h3 className="text-lg md:text-xl font-black text-slate-800">
                  实时 Agent 总结
                </h3>
                <p className="text-slate-400 text-xs md:text-sm font-medium">
                  配置偏好并启动即时分析
                </p>
              </div>
            </div>

            {/* Main content area - GPT chat-like */}
            <div className="flex-1 flex flex-col bg-white rounded-2xl md:rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
              {/* Top section - Group selection (standard mode only) */}
              {!boostMode && (
                <div className="border-b border-slate-200 bg-slate-50/60 p-3 md:p-4">
                  <div className="flex items-start gap-3">
                    <div className="pt-1 text-xs font-bold text-slate-600 whitespace-nowrap">
                      目标分组 <span className="text-rose-400">*</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex flex-wrap gap-2">
                        {allGroups.map((group) => (
                          <button
                            key={group.id}
                            onClick={() => toggleGroupForGen(group.id)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border whitespace-nowrap ${
                              selectedGroupsForGen.includes(group.id)
                                ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                                : 'bg-white text-slate-600 border-slate-300 hover:border-indigo-300'
                            }`}
                          >
                            {group.title}
                          </button>
                        ))}
                      </div>
                      {selectedGroupsForGen.length === 0 && (
                        <div className="mt-2 text-xs text-rose-400">
                          请至少选择一个分组
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Upper section - Focus input */}
              <div className="flex-1 flex flex-col p-4 md:p-6">
                <div className="flex-1 flex flex-col">
                  <div className="mb-3 flex items-center gap-2">
                    <label className="text-xs font-bold text-slate-600">
                      用户关注点
                    </label>
                    {boostMode && <span className="text-rose-400 text-xs">*</span>}
                    {!boostMode && <span className="text-slate-400 text-xs">(可选)</span>}
                  </div>
                  <textarea
                    value={generationFocus}
                    onChange={(e) => setGenerationFocus(e.target.value)}
                    placeholder={boostMode ? "请输入您的关注点..." : "例如：关注 AI 在移动端的应用..."}
                    className={`flex-1 w-full bg-slate-50 border-none rounded-xl md:rounded-2xl px-4 md:px-5 py-3 md:py-4 text-sm md:text-base focus:ring-2 focus:ring-indigo-500/20 resize-none outline-none ${
                      boostMode && !generationFocus.trim() ? 'ring-2 ring-rose-400' : ''
                    }`}
                    style={{ minHeight: '120px' }}
                  />
                  {boostMode && !generationFocus.trim() && (
                    <p className="text-xs text-rose-400 mt-2 ml-1">Boost Mode 下必须填写用户关注点</p>
                  )}
                </div>
              </div>

              {/* Lower section - Boost Mode toggle and controls */}
              <div className="border-t border-slate-200 bg-slate-50/50 px-3 py-2 md:px-4 md:py-2.5">
                <div className="flex items-center justify-between gap-3">
                  {/* Boost Mode toggle with info icon */}
                  <div className="flex items-center gap-3 flex-1">
                    <button
                      type="button"
                      onClick={() => {
                        setBoostMode(!boostMode);
                        // 切换到 boostMode 时清空已选择的分组
                        if (!boostMode) {
                          setSelectedGroupsForGen([]);
                        }
                      }}
                      className={`relative inline-flex h-6 w-10 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                        boostMode ? 'bg-indigo-600' : 'bg-slate-300'
                      }`}
                      role="switch"
                      aria-checked={boostMode}
                    >
                      <span
                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          boostMode ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                    
                    <span className="text-xs font-medium text-slate-700">
                      Boost Mode
                    </span>
                    
                    {/* Info icon with tooltip */}
                    <div className="relative group">
                      <Info 
                        size={16} 
                        className="text-slate-400 hover:text-slate-600 cursor-help transition-colors" 
                      />
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-0 mb-2 w-64 p-2.5 bg-slate-900 text-white text-[11px] rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none">
                        <div className="font-bold mb-1">
                          {boostMode ? 'Boost Mode' : 'Workflow'}
                        </div>
                        <div className="text-slate-300 leading-relaxed">
                          {boostMode 
                            ? 'BoostAgent 将自主选择所有可用订阅源，根据您的关注点智能生成内容。注意Token消耗会是workflow模式的两倍以上'
                            : 'Agentic Workflow，LLM智能筛选你选中的分组的当日更新，并生成简报。'
                          }
                        </div>
                        {/* Tooltip arrow */}
                        <div className="absolute top-full left-6 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-900" />
                      </div>
                    </div>
                  </div>

                  {/* Generate button */}
                  <button
                    onClick={startGeneration}
                    disabled={
                      (boostMode && !generationFocus.trim()) ||
                      (!boostMode && selectedGroupsForGen.length === 0)
                    }
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 text-xs md:text-sm whitespace-nowrap"
                  >
                    <PlayCircle size={16} />
                    启动
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default InstantLabPage;
