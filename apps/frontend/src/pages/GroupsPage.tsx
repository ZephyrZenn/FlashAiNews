import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Trash2,
  Edit3,
  FolderPlus,
} from 'lucide-react';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import { Layout } from '@/components/Layout';
import { Modal } from '@/components/Modal';
import { Select } from '@/components/ui/Select';
import type { Feed, FeedGroup } from '@/types/api';
import { useToast } from '@/context/ToastContext';
import { useConfirm } from '@/context/ConfirmDialogContext';

const GroupsPage = () => {
  const queryClient = useQueryClient();
  const { data: groups } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const { data: feeds } = useApiQuery<Feed[]>(queryKeys.feeds, api.getFeeds);
  const { showToast } = useToast();
  const { confirm } = useConfirm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<{
    id?: number;
    name: string;
    description: string;
    sources: number[];
  } | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<string>('');

  const allFeeds = feeds ?? [];
  const allGroups = groups ?? [];

  const createMutation = useApiMutation(async () => {
    if (!editingGroup) return;
    await api.createGroup({
      title: editingGroup.name,
      desc: editingGroup.description,
      feedIds: editingGroup.sources,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      setIsModalOpen(false);
      showToast('分组创建成功');
    },
    onError: (error) => {
      showToast(error.message || '创建分组失败', { type: 'error' });
    },
  });

  const updateMutation = useApiMutation(async () => {
    if (!editingGroup?.id) return;
    await api.updateGroup(editingGroup.id, {
      title: editingGroup.name,
      desc: editingGroup.description,
      feedIds: editingGroup.sources,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      setIsModalOpen(false);
      showToast('分组更新成功');
    },
    onError: (error) => {
      showToast(error.message || '更新分组失败', { type: 'error' });
    },
  });

  const deleteMutation = useApiMutation(async (groupId: number) => {
    await api.deleteGroup(groupId);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      showToast('分组删除成功');
    },
    onError: (error) => {
      showToast(error.message || '删除分组失败', { type: 'error' });
    },
  });

  const handleOpenModal = (group?: FeedGroup) => {
    if (group) {
      setEditingGroup({
        id: group.id,
        name: group.title,
        description: group.desc,
        sources: group.feeds.map((f) => f.id),
      });
    } else {
      setEditingGroup({ name: '', description: '', sources: [] });
    }
    setSelectedSourceId('');
    setIsModalOpen(true);
  };

  const handleDeleteGroup = async (groupId: number) => {
    const group = allGroups.find((g) => g.id === groupId);
    const confirmed = await confirm({
      title: '删除分组',
      description: `确定要删除"${group?.title ?? '此分组'}"吗？此操作无法撤销。`,
      confirmLabel: '删除',
      cancelLabel: '取消',
      tone: 'danger',
    });
    if (confirmed) {
      deleteMutation.mutate(groupId);
    }
  };

  const handleSaveGroup = () => {
    if (!editingGroup || !editingGroup.name) return;
    if (editingGroup.id) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  const handleRemoveSourceFromGroup = (sourceId: number) => {
    if (!editingGroup) return;
    setEditingGroup({
      ...editingGroup,
      sources: editingGroup.sources.filter((id) => id !== sourceId),
    });
  };

  const handleAddSourceToGroup = () => {
    if (!selectedSourceId || !editingGroup) return;
    const sourceId = parseInt(selectedSourceId);
    if (editingGroup.sources.includes(sourceId)) return;
    setEditingGroup({
      ...editingGroup,
      sources: [...editingGroup.sources, sourceId],
    });
    setSelectedSourceId('');
  };

  return (
    <Layout onNewClick={() => handleOpenModal()}>
      <div className="h-full overflow-y-auto p-10 custom-scrollbar grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 content-start">
        {allGroups.map((group) => (
          <div
            key={group.id}
            className="bg-white border border-slate-100 rounded-[2.5rem] p-8 shadow-sm hover:shadow-md transition-all relative group/card flex flex-col min-h-[220px]"
          >
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteGroup(group.id);
              }}
              className="absolute top-6 right-6 opacity-0 group-hover/card:opacity-100 p-2.5 text-rose-300 hover:text-rose-500 transition-all hover:bg-rose-50 rounded-2xl z-10"
            >
              <Trash2 size={18} />
            </button>
            <div className="flex-1 min-w-0 pr-6">
              <h3 className="text-xl font-black text-slate-800 mb-2 truncate">
                {group.title}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed line-clamp-3 mb-4">
                {group.desc || '暂无描述信息'}
              </p>
            </div>
            <div className="mt-auto pt-4 border-t border-slate-50 flex items-center justify-between shrink-0">
              <span className="text-[10px] font-black text-indigo-500 uppercase tracking-widest italic">
                {group.feeds?.length || 0} 个订阅源
              </span>
              <button
                onClick={() => handleOpenModal(group)}
                className="text-slate-300 hover:text-indigo-600 p-2 transition-colors"
              >
                <Edit3 size={18} />
              </button>
            </div>
          </div>
        ))}

        {/* Add new button */}
        <button
          onClick={() => handleOpenModal()}
          className="border-2 border-dashed border-slate-200 rounded-[2.5rem] p-6 flex flex-col items-center justify-center text-slate-300 hover:text-indigo-600 hover:bg-indigo-50/50 transition-all min-h-[220px]"
        >
          <FolderPlus size={36} strokeWidth={1.5} className="mb-2" />
          <span className="text-sm font-black uppercase">新建分组</span>
        </button>
      </div>

      {/* Modal - exactly matching t.tsx */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingGroup?.id ? '编辑分组' : '新建订阅分组'}
        onConfirm={handleSaveGroup}
      >
        <div className="space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-[12px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">
                分组名称
              </label>
              <input
                type="text"
                value={editingGroup?.name || ''}
                onChange={(e) =>
                  setEditingGroup((prev) =>
                    prev ? { ...prev, name: e.target.value } : null
                  )
                }
                className="w-full bg-slate-50 border-none rounded-2xl px-5 py-3 text-sm focus:ring-2 focus:ring-indigo-500/20 outline-none"
              />
            </div>
            <div>
              <label className="block text-[12px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">
                描述
              </label>
              <textarea
                value={editingGroup?.description || ''}
                onChange={(e) =>
                  setEditingGroup((prev) =>
                    prev ? { ...prev, description: e.target.value } : null
                  )
                }
                rows={2}
                className="w-full bg-slate-50 border-none rounded-2xl px-5 py-3 text-sm focus:ring-2 focus:ring-indigo-500/20 resize-none outline-none"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <label className="text-[12px] font-black text-slate-400 uppercase tracking-widest ml-1 mb-4 block">
              下属源管理
            </label>
            <div className="space-y-2 mb-4 max-h-40 overflow-y-auto custom-scrollbar">
              {(editingGroup?.sources || []).map((sourceId) => {
                const source = allFeeds.find((f) => f.id === sourceId);
                return (
                  source && (
                    <div
                      key={sourceId}
                      className="flex items-center justify-between p-3 bg-slate-50 rounded-xl"
                    >
                      <span className="text-sm font-bold">{source.title}</span>
                      <button
                        onClick={() => handleRemoveSourceFromGroup(sourceId)}
                        className="text-rose-400"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  )
                );
              })}
            </div>
            <div className="flex gap-2">
              <div className="flex-1">
                <Select
                  value={selectedSourceId}
                  onChange={(value) => setSelectedSourceId(value)}
                  placeholder="关联已有源..."
                  options={[
                    { value: '', label: '关联已有源...' },
                    ...allFeeds
                      .filter((f) => !(editingGroup?.sources || []).includes(f.id))
                      .map((f) => ({
                        value: f.id.toString(),
                        label: f.title,
                      })),
                  ]}
                  className="text-sm"
                />
              </div>
              <button
                onClick={handleAddSourceToGroup}
                className="bg-indigo-600 text-white px-4 py-2 rounded-xl hover:bg-indigo-700 transition-all shadow-sm hover:shadow-md active:scale-95"
              >
                <Plus size={16} />
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </Layout>
  );
};

export default GroupsPage;
