import { FormEvent, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Clock,
  Activity,
  Plus,
  X,
  Edit3,
  Trash2,
} from 'lucide-react';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import { useToast } from '@/context/ToastContext';
import { useConfirm } from '@/context/ConfirmDialogContext';
import type { Schedule, FeedGroup } from '@/types/api';

const SchedulesPage = () => {
  const queryClient = useQueryClient();
  const { data: schedules, isLoading } = useApiQuery<Schedule[]>(queryKeys.schedules, api.getSchedules);
  const { data: groups } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const { showToast } = useToast();
  const { confirm } = useConfirm();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);
  const [newTime, setNewTime] = useState('08:30');
  const [newFocus, setNewFocus] = useState('');
  const [newGroupIds, setNewGroupIds] = useState<number[]>([]);

  const createMutation = useApiMutation(async () => {
    return await api.createSchedule({
      time: newTime,
      focus: newFocus,
      groupIds: newGroupIds,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules });
      setIsCreateOpen(false);
      setNewTime('08:30');
      setNewFocus('');
      setNewGroupIds([]);
      showToast('计划创建成功');
    },
    onError: (error) => {
      showToast(error.message || '创建计划失败', { type: 'error' });
    },
  });

  const updateMutation = useApiMutation(async (variables: { scheduleId: string; payload: { time?: string; focus?: string; groupIds?: number[]; enabled?: boolean } }) => {
    return await api.updateSchedule(variables.scheduleId, variables.payload);
  }, {
    onMutate: async (variables) => {
      // Optimistic update for enabled toggle
      if (variables.payload.enabled !== undefined) {
        await queryClient.cancelQueries({ queryKey: queryKeys.schedules });
        const previousSchedules = queryClient.getQueryData<Schedule[]>(queryKeys.schedules);
        if (previousSchedules) {
          queryClient.setQueryData<Schedule[]>(queryKeys.schedules, (old) => {
            if (!old) return old;
            return old.map((s) =>
              s.id === variables.scheduleId ? { ...s, enabled: variables.payload.enabled! } : s
            );
          });
        }
        return { previousSchedules };
      }
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules });
      // Only close edit modal if we're not just toggling enabled
      if (variables.payload.enabled === undefined) {
        setEditingSchedule(null);
        showToast('计划更新成功');
      }
    },
    onError: (error, variables, context) => {
      // Rollback optimistic update on error
      if (context?.previousSchedules) {
        queryClient.setQueryData(queryKeys.schedules, context.previousSchedules);
      }
      showToast(error.message || '更新计划失败', { type: 'error' });
    },
  });

  const deleteMutation = useApiMutation(async (scheduleId: string) => {
    await api.deleteSchedule(scheduleId);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules });
      showToast('计划删除成功');
    },
    onError: (error) => {
      showToast(error.message || '删除计划失败', { type: 'error' });
    },
  });

  const toggleSchedule = async (schedule: Schedule) => {
    updateMutation.mutate({ scheduleId: schedule.id, payload: { enabled: !schedule.enabled } });
  };

  const handleDelete = async (schedule: Schedule) => {
    const confirmed = await confirm({
      title: '删除计划',
      description: `确定要删除 ${schedule.time} 的计划吗？此操作无法撤销。`,
      confirmLabel: '删除',
      cancelLabel: '取消',
      tone: 'danger',
    });
    if (confirmed) {
      deleteMutation.mutate(schedule.id);
    }
  };

  const handleCreateSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (newGroupIds.length === 0) {
      showToast('请至少选择一个分组', { type: 'error' });
      return;
    }
    createMutation.mutate();
  };

  const handleEditSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!editingSchedule) return;
    const payload: { time?: string; focus?: string; groupIds?: number[] } = {};
    if (newTime !== editingSchedule.time) payload.time = newTime;
    if (newFocus !== editingSchedule.focus) payload.focus = newFocus;
    if (JSON.stringify(newGroupIds.sort()) !== JSON.stringify(editingSchedule.groupIds.sort())) {
      payload.groupIds = newGroupIds;
    }
    if (Object.keys(payload).length > 0) {
      updateMutation.mutate({ scheduleId: editingSchedule.id, payload });
    } else {
      setEditingSchedule(null);
    }
  };

  const openCreateModal = () => {
    setNewTime('08:30');
    setNewFocus('');
    setNewGroupIds([]);
    setIsCreateOpen(true);
  };

  const openEditModal = (schedule: Schedule) => {
    setEditingSchedule(schedule);
    setNewTime(schedule.time);
    setNewFocus(schedule.focus);
    setNewGroupIds([...schedule.groupIds]);
  };

  const toggleGroupSelection = (groupId: number) => {
    setNewGroupIds((prev) =>
      prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId]
    );
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-700 h-full flex flex-col min-h-0">
      <div className="flex justify-between items-end border-b border-white/5 pb-8 flex-shrink-0">
        <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase leading-none italic">
          自动生成计划
        </h2>
        <button
          onClick={openCreateModal}
          className="px-6 py-3 bg-white text-black rounded-xl font-black flex items-center gap-2 hover:bg-cyan-400 transition-all shadow-xl uppercase text-[10px] tracking-widest"
        >
          <Plus size={14} /> 新建计划
        </button>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-10">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-slate-500 text-sm">加载计划中...</div>
          </div>
        ) : !schedules || schedules.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
            <div className="bg-slate-900/40 border border-white/10 rounded-[3rem] p-12 text-center max-w-md">
              <div className="mb-6">
                <Clock size={48} className="text-slate-600 mx-auto mb-4" />
                <Activity size={32} className="text-slate-600 mx-auto" />
              </div>
              <h3 className="text-xl font-black text-white italic tracking-tighter uppercase mb-4">
                暂无计划
              </h3>
              <p className="text-slate-500 text-sm mb-4">
                创建您的第一个自动化计划以自动生成简报。
              </p>
              <button
                onClick={openCreateModal}
                className="px-6 py-3 bg-white text-black rounded-xl font-black hover:bg-cyan-400 transition-all uppercase text-[10px] tracking-widest"
              >
                创建计划
              </button>
            </div>
          </div>
        ) : (
          <div className="grid gap-6">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                className={`p-8 bg-slate-900/40 border rounded-[3rem] flex flex-col md:flex-row gap-8 items-center transition-all ${
                  schedule.enabled
                    ? 'border-cyan-500/20 shadow-2xl'
                    : 'border-white/5 opacity-30'
                }`}
              >
                <div className="bg-black border border-white/10 p-8 rounded-[2rem] text-center min-w-[140px] shadow-inner">
                  <Clock className="text-cyan-500 mx-auto mb-3" size={28} />
                  <div className="text-4xl font-black text-white leading-none tracking-tighter italic">
                    {schedule.time}
                  </div>
                </div>
                <div className="flex-1 space-y-5 italic">
                  <div className="flex flex-wrap gap-2">
                    {schedule.groupIds.map((gid) => {
                      const group = groups?.find((g) => g.id === gid);
                      return (
                        <span
                          key={gid}
                          className="px-4 py-1.5 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-full text-sm font-black uppercase tracking-widest"
                        >
                          {group?.title || `Group ${gid}`}
                        </span>
                      );
                    })}
                  </div>
                  <p className="text-slate-300 font-light text-base pl-6 border-l-2 border-white/5 leading-relaxed italic opacity-80">
                    &quot;{schedule.focus || '未指定焦点'}&quot;
                  </p>
                </div>
                <div className="flex items-center gap-6 border-l border-white/5 pl-10">
                  <div className="flex flex-col gap-4">
                    <div
                      onClick={() => toggleSchedule(schedule)}
                      className="w-16 h-8 bg-black rounded-full border border-white/10 relative p-1 cursor-pointer overflow-hidden shadow-inner flex-shrink-0"
                    >
                      <div
                        className={`w-6 h-6 rounded-full transition-all duration-700 flex items-center justify-center ${
                          schedule.enabled
                            ? 'bg-cyan-500 translate-x-8 shadow-[0_0_20px_cyan]'
                            : 'bg-slate-800 translate-x-0'
                        }`}
                      >
                        {schedule.enabled ? <Activity size={10} className="text-white" /> : null}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEditModal(schedule)}
                        className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-cyan-400 transition-all"
                      >
                        <Edit3 size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(schedule)}
                        className="p-2 bg-white/5 hover:bg-red-500/10 rounded-lg text-slate-400 hover:text-red-500 transition-all"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 w-full max-w-md shadow-2xl animate-in zoom-in duration-300">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter italic">
                新建计划
              </h3>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="text-[16px] font-black text-cyan-400 uppercase tracking-[0.3em] mb-2 block">
                  时间
                </label>
                <input
                  type="time"
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-3 text-white font-mono text-[14px] outline-none focus:border-cyan-500 transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[16px] font-black text-purple-400 uppercase tracking-[0.3em] mb-2 block">
                  关注点
                </label>
                <textarea
                  value={newFocus}
                  onChange={(e) => setNewFocus(e.target.value)}
                  placeholder="想了解点什么..."
                  className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-3 text-white font-mono text-[14px] outline-none focus:border-purple-500 transition-all resize-none"
                  rows={3}
                />
              </div>
              <div>
                <label className="text-[16px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-2 block">
                  分组
                </label>
                <div className="max-h-40 overflow-y-auto custom-scrollbar space-y-2 bg-black/40 p-3 rounded-xl border border-white/5">
                  {groups?.map((group) => (
                    <label
                      key={group.id}
                      className="flex items-center gap-2 text-white text-[14px] cursor-pointer hover:text-cyan-400 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={newGroupIds.includes(group.id)}
                        onChange={() => toggleGroupSelection(group.id)}
                        className="rounded"
                      />
                      <span>{group.title}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 mt-8">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="flex-1 py-2.5 bg-white/5 text-white font-black rounded-2xl uppercase text-[10px] tracking-widest hover:bg-white/10 transition-all"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-white text-black font-black rounded-2xl uppercase text-[10px] tracking-widest shadow-xl hover:bg-cyan-400 transition-all active:scale-95"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? '创建中...' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingSchedule && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 w-full max-w-md shadow-2xl animate-in zoom-in duration-300">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter italic">
                编辑计划
              </h3>
              <button
                onClick={() => setEditingSchedule(null)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="text-[16px] font-black text-cyan-400 uppercase tracking-[0.3em] mb-2 block">
                  时间
                </label>
                <input
                  type="time"
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-3 text-white font-mono text-[14px] outline-none focus:border-cyan-500 transition-all"
                  required
                />
              </div>
              <div>
                <label className="text-[16px] font-black text-purple-400 uppercase tracking-[0.3em] mb-2 block">
                  关注点
                </label>
                <textarea
                  value={newFocus}
                  onChange={(e) => setNewFocus(e.target.value)}
                  placeholder="想了解点什么..."
                  className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-3 text-white font-mono text-[14px] outline-none focus:border-purple-500 transition-all resize-none"
                  rows={3}
                />
              </div>
              <div>
                <label className="text-[16px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-2 block">
                  分组
                </label>
                <div className="max-h-40 overflow-y-auto custom-scrollbar space-y-2 bg-black/40 p-3 rounded-xl border border-white/5">
                  {groups?.map((group) => (
                    <label
                      key={group.id}
                      className="flex items-center gap-2 text-white text-[14px] cursor-pointer hover:text-cyan-400 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={newGroupIds.includes(group.id)}
                        onChange={() => toggleGroupSelection(group.id)}
                        className="rounded"
                      />
                      <span>{group.title}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 mt-8">
                <button
                  type="button"
                  onClick={() => setEditingSchedule(null)}
                  className="flex-1 py-2.5 bg-white/5 text-white font-black rounded-2xl uppercase text-[10px] tracking-widest hover:bg-white/10 transition-all"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-white text-black font-black rounded-2xl uppercase text-[10px] tracking-widest shadow-xl hover:bg-cyan-400 transition-all active:scale-95"
                  disabled={updateMutation.isPending}
                >
                  {updateMutation.isPending ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulesPage;
