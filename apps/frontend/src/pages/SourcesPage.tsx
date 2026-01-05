import { FormEvent, useEffect, useMemo, useState, useRef, ChangeEvent } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Settings,
  Edit3,
  Trash2,
  X,
} from 'lucide-react';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import type { Feed, FeedGroup } from '@/types/api';
import { useToast } from '@/context/ToastContext';
import { useConfirm } from '@/context/ConfirmDialogContext';

// Color palette for group card headers
const groupColorPalettes = [
  'from-blue-500 to-cyan-400',
  'from-purple-500 to-pink-400',
  'from-indigo-500 to-blue-400',
  'from-cyan-500 to-teal-400',
  'from-amber-500 to-orange-400',
  'from-emerald-500 to-green-400',
  'from-rose-500 to-pink-400',
  'from-violet-500 to-purple-400',
];

const getGroupColor = (groupId: number): string => {
  return groupColorPalettes[groupId % groupColorPalettes.length];
};

const SourcesPage = () => {
  const queryClient = useQueryClient();
  const [subTab, setSubTab] = useState<'groups' | 'feeds'>('groups');
  const groupsQuery = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const feedsQuery = useApiQuery<Feed[]>(queryKeys.feeds, api.getFeeds);
  const { showToast } = useToast();
  const { confirm } = useConfirm();

  // Groups state
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editFeedIds, setEditFeedIds] = useState<number[]>([]);
  const [isCreateGroupOpen, setIsCreateGroupOpen] = useState(false);
  const [newGroupTitle, setNewGroupTitle] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newGroupFeedIds, setNewGroupFeedIds] = useState<number[]>([]);

  // Feeds state
  const [selectedFeedId, setSelectedFeedId] = useState<number | null>(null);
  const [editFeedTitle, setEditFeedTitle] = useState('');
  const [editFeedUrl, setEditFeedUrl] = useState('');
  const [editFeedDesc, setEditFeedDesc] = useState('');
  const [isCreateFeedOpen, setIsCreateFeedOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [newFeedTitle, setNewFeedTitle] = useState('');
  const [newFeedUrl, setNewFeedUrl] = useState('');
  const [newFeedDesc, setNewFeedDesc] = useState('');
  const [opmlUrl, setOpmlUrl] = useState('');
  const [opmlContent, setOpmlContent] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const groupDetailQuery = useApiQuery<FeedGroup>(
    queryKeys.groupDetail(selectedGroupId ?? -1),
    () => api.getGroupDetail(selectedGroupId ?? -1),
    { enabled: Boolean(selectedGroupId) },
  );

  const selectedGroup = groupDetailQuery.data;
  const allFeeds: Feed[] = feedsQuery.data ?? [];
  const groups: FeedGroup[] = groupsQuery.data ?? [];

  useEffect(() => {
    if (selectedGroup) {
      setEditTitle(selectedGroup.title);
      setEditDesc(selectedGroup.desc);
      setEditFeedIds(selectedGroup.feeds.map((feed) => feed.id));
    }
  }, [selectedGroup]);

  useEffect(() => {
    const target = allFeeds.find((feed) => feed.id === selectedFeedId);
    if (target) {
      setEditFeedTitle(target.title);
      setEditFeedUrl(target.url);
      setEditFeedDesc(target.desc);
    }
  }, [selectedFeedId, allFeeds]);

  // Group mutations
  const updateGroupMutation = useApiMutation(async () => {
    if (!selectedGroupId) return;
    await api.updateGroup(selectedGroupId, {
      title: editTitle,
      desc: editDesc,
      feedIds: editFeedIds,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      if (selectedGroupId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.groupDetail(selectedGroupId) });
      }
      setSelectedGroupId(null);
      showToast('分组更新成功');
    },
    onError: (error) => {
      showToast(error.message || '更新分组失败', { type: 'error' });
    },
  });

  const createGroupMutation = useApiMutation(async () => {
    const newId = await api.createGroup({
      title: newGroupTitle,
      desc: newGroupDesc,
      feedIds: newGroupFeedIds,
    });
    return newId;
  }, {
    onSuccess: (gid) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      if (gid) setSelectedGroupId(gid);
      setIsCreateGroupOpen(false);
      showToast('分组创建成功');
    },
    onError: (error) => {
      showToast(error.message || '创建分组失败', { type: 'error' });
    },
  });

  const deleteGroupMutation = useApiMutation(async (groupId: number) => {
    await api.deleteGroup(groupId);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      setSelectedGroupId(null);
      showToast('分组删除成功');
    },
    onError: (error) => {
      showToast(error.message || '删除分组失败', { type: 'error' });
    },
  });

  // Feed mutations
  const updateFeedMutation = useApiMutation(async () => {
    if (!selectedFeedId) return;
    await api.updateFeed(selectedFeedId, {
      title: editFeedTitle,
      url: editFeedUrl,
      desc: editFeedDesc,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
      showToast('订阅源更新成功');
    },
    onError: (error) => {
      showToast(error.message || '更新订阅源失败', { type: 'error' });
    },
  });

  const createFeedMutation = useApiMutation(async () => {
    await api.createFeed({ title: newFeedTitle, url: newFeedUrl, desc: newFeedDesc });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
      setIsCreateFeedOpen(false);
      setNewFeedTitle('');
      setNewFeedUrl('');
      setNewFeedDesc('');
      showToast('订阅源创建成功');
    },
    onError: (error) => {
      showToast(error.message || '创建订阅源失败', { type: 'error' });
    },
  });

  const deleteFeedMutation = useApiMutation(async (feedId: number) => {
    await api.deleteFeed(feedId);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
      setSelectedFeedId(null);
      showToast('订阅源删除成功');
    },
    onError: (error) => {
      showToast(error.message || '删除订阅源失败', { type: 'error' });
    },
  });

  const importFeedsMutation = useApiMutation(async () => {
    await api.importFeeds({
      url: opmlUrl.trim() || undefined,
      content: opmlContent.trim() || undefined,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
      setIsImportOpen(false);
      setOpmlUrl('');
      setOpmlContent('');
      showToast('订阅源导入成功');
    },
    onError: (error) => {
      showToast(error.message || '导入订阅源失败', { type: 'error' });
    },
  });

  const handleDeleteGroup = async () => {
    if (!selectedGroupId) return;
    const group = groups.find((g) => g.id === selectedGroupId);
    const confirmed = await confirm({
      title: '删除分组',
      description: `确定要删除"${group?.title ?? '此分组'}"吗？此操作无法撤销。`,
      confirmLabel: '删除',
      cancelLabel: '取消',
      tone: 'danger',
    });
    if (confirmed) deleteGroupMutation.mutate(selectedGroupId);
  };

  const handleDeleteFeed = async (feedId: number) => {
    const feed = allFeeds.find((f) => f.id === feedId);
    const confirmed = await confirm({
      title: '删除订阅源',
      description: `确定要删除"${feed?.title ?? '此订阅源'}"吗？此操作无法撤销。`,
      confirmLabel: '删除',
      cancelLabel: '取消',
      tone: 'danger',
    });
    if (confirmed) deleteFeedMutation.mutate(feedId);
  };

  const handleOpmlFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result === 'string') {
        setOpmlContent(result);
        setOpmlUrl('');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  const getGroupFeedCount = (groupId: number) => {
    return allFeeds.filter((f) => {
      const group = groups.find((g) => g.id === groupId);
      return group?.feeds.some((gf) => gf.id === f.id);
    }).length;
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-700 h-full flex flex-col min-h-0">
      <div className="flex justify-between items-end border-b border-white/5 pb-8 flex-shrink-0">
        <div>
          <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase leading-none italic">
            Sources_Config
          </h2>
          <p className="text-slate-500 text-[10px] font-mono uppercase tracking-[0.4em] mt-3">
            Distribution Protocols & Endpoints
          </p>
        </div>
        <div className="flex gap-2 bg-white/5 p-1 rounded-2xl">
          <button
            onClick={() => setSubTab('groups')}
            className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
              subTab === 'groups'
                ? 'bg-white text-black shadow-lg'
                : 'text-slate-500 hover:text-white'
            }`}
          >
            分组
          </button>
          <button
            onClick={() => setSubTab('feeds')}
            className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
              subTab === 'feeds'
                ? 'bg-white text-black shadow-lg'
                : 'text-slate-500 hover:text-white'
            }`}
          >
            订阅源
          </button>
        </div>
      </div>

      {subTab === 'groups' ? (
        <div className="flex-1 overflow-y-auto custom-scrollbar animate-in slide-in-from-right-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 pb-10">
            {groups.map((group) => (
              <div
                key={group.id}
                className="bg-slate-900/30 border border-white/5 rounded-[2.5rem] overflow-hidden hover:border-cyan-500/20 transition-all group shadow-inner relative"
              >
                <div className={`p-6 bg-gradient-to-r ${getGroupColor(group.id)} bg-opacity-10 border-b border-white/5 flex justify-between items-center`}>
                  <span className="font-black text-white text-[16px] uppercase tracking-widest italic">
                    {group.title}
                  </span>
                  <button 
                    onClick={() => setSelectedGroupId(group.id)}
                    className="p-2 text-white/30 hover:text-white transition-all bg-black/20 rounded-lg group-hover:bg-cyan-500/20"
                  >
                    <Settings size={14} />
                  </button>
                </div>
                <div className="p-6 flex justify-between items-center">
                  <span className="text-[14px] text-slate-500 font-mono uppercase tracking-widest">
                    追踪订阅源
                  </span>
                  <span className="text-xl font-black text-white">{group.feeds.length}</span>
                </div>
              </div>
            ))}
            <button
              onClick={() => setIsCreateGroupOpen(true)}
              className="border-2 border-dashed border-white/5 rounded-[2.5rem] flex flex-col items-center justify-center gap-4 text-slate-700 hover:text-cyan-400 transition-all min-h-[160px] group/new"
            >
              <Plus size={24} className="group-hover/new:scale-110 transition-transform" />
              <span className="text-[16px] font-black uppercase tracking-[0.2em]">新建分组</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col min-h-0 animate-in slide-in-from-right-4">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.3em]">
              授权订阅源注册表
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => setIsImportOpen(true)}
                className="px-5 py-2 bg-white/5 text-white rounded-xl font-black flex items-center gap-2 hover:bg-white/10 transition-all uppercase text-[9px] tracking-widest border border-white/5"
              >
                <Plus size={12} /> 导入
              </button>
              <button
                onClick={() => setIsCreateFeedOpen(true)}
                className="px-5 py-2 bg-white text-black rounded-xl font-black flex items-center gap-2 hover:bg-cyan-400 transition-all shadow-xl uppercase text-[9px] tracking-widest"
              >
                <Plus size={12} /> 添加订阅源
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar pb-10">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {allFeeds.map((feed) => (
                <div
                  key={feed.id}
                  className="bg-slate-900/40 border border-white/5 rounded-2xl p-4 hover:border-cyan-500/20 transition-all group flex flex-col relative overflow-hidden"
                >
                  <div className="flex-1 min-w-0 mb-4">
                    <h4 className="text-sm font-black text-white truncate uppercase tracking-tight italic">
                      {feed.title}
                    </h4>
                    {feed.desc && (
                      <p className="text-xs text-slate-400 mt-2 line-clamp-2 italic">
                        {feed.desc}
                      </p>
                    )}
                  </div>
                  <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all">
                    <button
                      onClick={() => setSelectedFeedId(feed.id)}
                      className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-cyan-400 transition-all"
                    >
                      <Edit3 size={14} />
                    </button>
                    <button
                      onClick={() => handleDeleteFeed(feed.id)}
                      className="p-2 bg-white/5 hover:bg-red-500/10 rounded-lg text-slate-400 hover:text-red-500 transition-all"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  <div className="absolute top-0 left-0 w-1 h-0 group-hover:h-full bg-cyan-500 transition-all duration-300"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Create Group Modal */}
      {isCreateGroupOpen && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 w-full max-w-md shadow-2xl animate-in zoom-in duration-300">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter italic">
                新建分组
              </h3>
              <button
                onClick={() => setIsCreateGroupOpen(false)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <form
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                createGroupMutation.mutate();
              }}
              className="space-y-4"
            >
              <input
                value={newGroupTitle}
                onChange={(e) => setNewGroupTitle(e.target.value)}
                type="text"
                placeholder="分组名称..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px]"
                required
              />
              <textarea
                value={newGroupDesc}
                onChange={(e) => setNewGroupDesc(e.target.value)}
                placeholder="描述..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px] resize-none"
                rows={3}
              />
              <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                {allFeeds.map((feed) => (
                  <label key={feed.id} className="flex items-center gap-2 text-white text-[14px]">
                    <input
                      type="checkbox"
                      checked={newGroupFeedIds.includes(feed.id)}
                      onChange={() => {
                        setNewGroupFeedIds((prev) =>
                          prev.includes(feed.id)
                            ? prev.filter((id) => id !== feed.id)
                            : [...prev, feed.id]
                        );
                      }}
                      className="rounded"
                    />
                    <span>{feed.title}</span>
                  </label>
                ))}
              </div>
              <button
                type="submit"
                className="w-full mt-8 py-2.5 bg-white text-black font-black rounded-2xl uppercase text-[16px] tracking-widest shadow-xl hover:bg-cyan-400 transition-all active:scale-95"
                disabled={createGroupMutation.isPending}
              >
                {createGroupMutation.isPending ? '创建中...' : '创建分组'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Create Feed Modal */}
      {isCreateFeedOpen && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 w-full max-w-md shadow-2xl animate-in zoom-in duration-300">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter italic">
                新建订阅源
              </h3>
              <button
                onClick={() => setIsCreateFeedOpen(false)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <form
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                createFeedMutation.mutate();
              }}
              className="space-y-4"
            >
              <input
                value={newFeedTitle}
                onChange={(e) => setNewFeedTitle(e.target.value)}
                type="text"
                placeholder="订阅源名称..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px]"
                required
              />
              <input
                value={newFeedUrl}
                onChange={(e) => setNewFeedUrl(e.target.value)}
                type="url"
                placeholder="端点 URL..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px]"
                required
              />
              <textarea
                value={newFeedDesc}
                onChange={(e) => setNewFeedDesc(e.target.value)}
                placeholder="描述..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px] resize-none"
                rows={2}
              />
              <button
                type="submit"
                className="w-full mt-8 py-2.5 bg-white text-black font-black rounded-2xl uppercase text-[10px] tracking-widest shadow-xl hover:bg-cyan-400 transition-all active:scale-95"
                disabled={createFeedMutation.isPending}
              >
                {createFeedMutation.isPending ? '创建中...' : '连接协议'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Edit Feed Modal */}
      {selectedFeedId && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 w-full max-w-md shadow-2xl animate-in zoom-in duration-300">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter italic">
                编辑订阅源
              </h3>
              <button
                onClick={() => setSelectedFeedId(null)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <form
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                updateFeedMutation.mutate();
              }}
              className="space-y-4"
            >
              <input
                value={editFeedTitle}
                onChange={(e) => setEditFeedTitle(e.target.value)}
                type="text"
                placeholder="订阅源名称..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px]"
                required
              />
              <input
                value={editFeedUrl}
                onChange={(e) => setEditFeedUrl(e.target.value)}
                type="url"
                placeholder="端点 URL..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px]"
                required
              />
              <textarea
                value={editFeedDesc}
                onChange={(e) => setEditFeedDesc(e.target.value)}
                placeholder="描述..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-[14px] resize-none"
                rows={2}
              />
              <div className="flex gap-2 mt-8">
                <button
                  type="button"
                  onClick={() => setSelectedFeedId(null)}
                  className="flex-1 py-2.5 bg-white/5 text-white font-black rounded-2xl uppercase text-[16px] tracking-widest hover:bg-white/10 transition-all"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-white text-black font-black rounded-2xl uppercase text-[10px] tracking-widest shadow-xl hover:bg-cyan-400 transition-all active:scale-95"
                  disabled={updateFeedMutation.isPending}
                >
                  {updateFeedMutation.isPending ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import OPML Modal */}
      {isImportOpen && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 w-full max-w-md shadow-2xl animate-in zoom-in duration-300">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter italic">
                导入 OPML
              </h3>
              <button
                onClick={() => setIsImportOpen(false)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <form
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                importFeedsMutation.mutate();
              }}
              className="space-y-4"
            >
              <input
                value={opmlUrl}
                onChange={(e) => setOpmlUrl(e.target.value)}
                type="url"
                placeholder="OPML URL..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-xs"
              />
              <textarea
                value={opmlContent}
                onChange={(e) => setOpmlContent(e.target.value)}
                placeholder="OPML 内容..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-xs resize-none"
                rows={6}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-3 bg-white/5 text-white font-black rounded-2xl uppercase text-[10px] tracking-widest hover:bg-white/10 transition-all border border-white/5"
              >
                上传文件
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".opml,.xml"
                onChange={handleOpmlFileSelect}
                className="hidden"
              />
              <button
                type="submit"
                className="w-full mt-8 py-2.5 bg-white text-black font-black rounded-2xl uppercase text-[10px] tracking-widest shadow-xl hover:bg-cyan-400 transition-all active:scale-95"
                disabled={importFeedsMutation.isPending || (!opmlUrl && !opmlContent)}
              >
                {importFeedsMutation.isPending ? '导入中...' : '导入订阅源'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Edit Group Modal */}
      {selectedGroupId && selectedGroup && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-white/10 rounded-[2.5rem] p-10 w-full max-w-md shadow-2xl animate-in zoom-in duration-300">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-white/5">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter italic">
                编辑分组
              </h3>
              <button
                onClick={() => setSelectedGroupId(null)}
                className="text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <form
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                updateGroupMutation.mutate();
              }}
              className="space-y-4"
            >
              <input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                type="text"
                placeholder="分组名称..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-xs"
                required
              />
              <textarea
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                placeholder="描述..."
                className="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-3 outline-none text-white focus:border-cyan-500 transition-all font-mono text-xs resize-none"
                rows={3}
              />
              <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                {allFeeds.map((feed) => (
                  <label key={feed.id} className="flex items-center gap-2 text-white text-xs">
                    <input
                      type="checkbox"
                      checked={editFeedIds.includes(feed.id)}
                      onChange={() => {
                        setEditFeedIds((prev) =>
                          prev.includes(feed.id)
                            ? prev.filter((id) => id !== feed.id)
                            : [...prev, feed.id]
                        );
                      }}
                      className="rounded"
                    />
                    <span>{feed.title}</span>
                  </label>
                ))}
              </div>
              <div className="flex gap-2 mt-8">
                <button
                  type="button"
                  onClick={() => setSelectedGroupId(null)}
                  className="flex-1 py-2.5 bg-white/5 text-white font-black rounded-2xl uppercase text-[10px] tracking-widest hover:bg-white/10 transition-all"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-white text-black font-black rounded-2xl uppercase text-[10px] tracking-widest shadow-xl hover:bg-cyan-400 transition-all active:scale-95"
                  disabled={updateGroupMutation.isPending}
                >
                  {updateGroupMutation.isPending ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SourcesPage;

