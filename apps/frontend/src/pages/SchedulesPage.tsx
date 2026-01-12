import { useState, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Trash2,
  Edit3,
  Power,
  Activity,
} from 'lucide-react';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import { Layout } from '@/components/Layout';
import { Modal } from '@/components/Modal';
import type { Schedule, FeedGroup } from '@/types/api';
import { useToast } from '@/context/ToastContext';
import { useConfirm } from '@/context/ConfirmDialogContext';

const SchedulesPage = () => {
  const queryClient = useQueryClient();
  const { data: schedules } = useApiQuery<Schedule[]>(queryKeys.schedules, api.getSchedules);
  const { data: groups } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const { showToast } = useToast();
  const { confirm } = useConfirm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<{
    id?: string;
    time: string;
    groupIds: number[];
    focus: string;
    active: boolean;
  } | null>(null);

  const allSchedules = schedules ?? [];
  const allGroups = groups ?? [];

  // Create a map from group id to group for quick lookup
  const groupMap = useMemo(() => {
    const map = new Map<number, FeedGroup>();
    allGroups.forEach((g) => map.set(g.id, g));
    return map;
  }, [allGroups]);

  const createMutation = useApiMutation(async () => {
    if (!editingSchedule) return;
    await api.createSchedule({
      time: editingSchedule.time,
      groupIds: editingSchedule.groupIds,
      focus: editingSchedule.focus,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules });
      setIsModalOpen(false);
      showToast('定时任务创建成功');
    },
    onError: (error) => {
      showToast(error.message || '创建定时任务失败', { type: 'error' });
    },
  });

  const updateMutation = useApiMutation(async () => {
    if (!editingSchedule?.id) return;
    await api.updateSchedule(editingSchedule.id, {
      time: editingSchedule.time,
      groupIds: editingSchedule.groupIds,
      focus: editingSchedule.focus,
      enabled: editingSchedule.active,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules });
      setIsModalOpen(false);
      showToast('定时任务更新成功');
    },
    onError: (error) => {
      showToast(error.message || '更新定时任务失败', { type: 'error' });
    },
  });

  const deleteMutation = useApiMutation(async (scheduleId: string) => {
    await api.deleteSchedule(scheduleId);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules });
      showToast('定时任务删除成功');
    },
    onError: (error) => {
      showToast(error.message || '删除定时任务失败', { type: 'error' });
    },
  });

  const toggleMutation = useApiMutation(async (schedule: Schedule) => {
    await api.updateSchedule(schedule.id, {
      enabled: !schedule.enabled,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules });
    },
  });

  const handleOpenModal = (schedule?: Schedule) => {
    if (schedule) {
      setEditingSchedule({
        id: schedule.id,
        time: schedule.time,
        groupIds: schedule.groupIds,
        focus: schedule.focus || '',
        active: schedule.enabled,
      });
    } else {
      setEditingSchedule({ time: '08:00', groupIds: [], focus: '', active: true });
    }
    setIsModalOpen(true);
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    const confirmed = await confirm({
      title: '删除定时任务',
      description: '确定要删除此定时任务吗？此操作无法撤销。',
      confirmLabel: '删除',
      cancelLabel: '取消',
      tone: 'danger',
    });
    if (confirmed) {
      deleteMutation.mutate(scheduleId);
    }
  };

  const handleSaveSchedule = () => {
    if (!editingSchedule || !editingSchedule.time) return;
    if (editingSchedule.id) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  const handleToggleSchedule = (schedule: Schedule) => {
    toggleMutation.mutate(schedule);
  };

  const toggleGroupInSchedule = (groupId: number) => {
    if (!editingSchedule) return;
    const current = editingSchedule.groupIds;
    const updated = current.includes(groupId)
      ? current.filter((id) => id !== groupId)
      : [...current, groupId];
    setEditingSchedule({ ...editingSchedule, groupIds: updated });
  };

  return (
    <Layout onNewClick={() => handleOpenModal()}>
      <div className="h-full overflow-y-auto p-12 custom-scrollbar">
        <div className="max-w-5xl mx-auto space-y-6">
          {allSchedules.map((task) => {
            const isActive = task.enabled;
            
            return (
              <div
                key={task.id}
                className={`bg-white rounded-[2.5rem] border transition-all duration-500 flex items-center p-8 gap-8 shadow-sm group relative ${
                  isActive
                    ? 'border-slate-100'
                    : 'border-slate-50 opacity-60 bg-slate-50/50'
                }`}
              >
                {/* Time display */}
                <div className="flex flex-col items-center shrink-0 w-24">
                  <span
                    className={`text-3xl font-black transition-all ${
                      isActive ? 'text-slate-800' : 'text-slate-400'
                    }`}
                  >
                    {task.time}
                  </span>
                  <div
                    className={`mt-2 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-600 animate-pulse'
                        : 'bg-slate-200 text-slate-500'
                    }`}
                  >
                    {isActive ? 'Next Run' : 'Paused'}
                  </div>
                </div>

                <div className="h-12 w-[1px] bg-slate-100 hidden md:block" />

                {/* Content */}
                <div className="flex-1 min-w-0 space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {task.groupIds.map((gid) => {
                      const group = groupMap.get(gid);
                      return (
                        <span
                          key={gid}
                          className={`px-3 py-1 border rounded-xl text-[10px] font-bold transition-all ${
                            isActive
                              ? 'bg-white border-indigo-100 text-indigo-500 shadow-sm'
                              : 'bg-transparent border-slate-200 text-slate-400'
                          }`}
                        >
                          {group?.title || `分组 ${gid}`}
                        </span>
                      );
                    })}
                  </div>
                  <div className="flex items-start gap-2">
                    <Activity
                      size={14}
                      className={
                        isActive
                          ? 'text-indigo-300 mt-0.5'
                          : 'text-slate-300 mt-0.5'
                      }
                    />
                    <p
                      className={`text-sm font-medium leading-relaxed truncate max-w-md ${
                        isActive ? 'text-slate-500' : 'text-slate-300'
                      }`}
                    >
                      {task.focus || '默认广度总结模式'}
                    </p>
                  </div>
                </div>

                {/* Controls */}
                <div className="flex items-center gap-6">
                  <div className="flex flex-col items-center gap-2">
                    <button
                      onClick={() => handleToggleSchedule(task)}
                      className={`relative w-20 h-10 rounded-full transition-all duration-300 flex items-center px-1 shadow-inner ${
                        isActive ? 'bg-emerald-500' : 'bg-slate-300'
                      }`}
                    >
                      <div
                        className={`absolute transition-all duration-300 h-8 w-8 rounded-full bg-white shadow-md flex items-center justify-center ${
                          isActive ? 'translate-x-10' : 'translate-x-0'
                        }`}
                      >
                        <Power
                          size={14}
                          className={
                            isActive ? 'text-emerald-500' : 'text-slate-400'
                          }
                        />
                      </div>
                    </button>
                  </div>
                  <div className="h-10 w-[1px] bg-slate-100" />
                  <div className="flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <button
                      onClick={() => handleOpenModal(task)}
                      className="p-2.5 text-slate-300 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
                    >
                      <Edit3 size={18} />
                    </button>
                    <button
                      onClick={() => handleDeleteSchedule(task.id)}
                      className="p-2.5 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Add new button */}
          <button
            onClick={() => handleOpenModal()}
            className="w-full py-12 border-2 border-dashed border-slate-200 rounded-[3rem] flex flex-col items-center justify-center text-slate-300 hover:text-indigo-600 transition-all gap-3"
          >
            <Plus size={36} />
            <span className="text-sm font-black uppercase tracking-[0.2em]">
              新建自动化方案
            </span>
          </button>
        </div>
      </div>

      {/* Modal - matching t.tsx schedule modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingSchedule?.id ? '编辑策略' : '新建策略'}
        onConfirm={handleSaveSchedule}
      >
        <div className="space-y-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">
                执行时间
              </label>
              <input
                type="time"
                value={editingSchedule?.time || ''}
                onChange={(e) =>
                  setEditingSchedule((prev) =>
                    prev ? { ...prev, time: e.target.value } : null
                  )
                }
                className="w-full bg-slate-50 border-none rounded-2xl px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500/20 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">
              涉及分组
            </label>
            <div className="flex flex-wrap gap-2">
              {allGroups.map((g) => (
                <button
                  key={g.id}
                  onClick={() => toggleGroupInSchedule(g.id)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                    editingSchedule?.groupIds.includes(g.id)
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-slate-400 border-slate-100'
                  }`}
                >
                  {g.title}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">
              关注点
            </label>
            <textarea
              value={editingSchedule?.focus || ''}
              onChange={(e) =>
                setEditingSchedule((prev) =>
                  prev ? { ...prev, focus: e.target.value } : null
                )
              }
              rows={2}
              className="w-full bg-slate-50 border-none rounded-2xl px-5 py-3 text-sm resize-none outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
        </div>
      </Modal>
    </Layout>
  );
};

export default SchedulesPage;
