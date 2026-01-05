import { useEffect, useMemo, useState } from 'react';
import {
  ChevronRight,
  FileText,
  ArrowRight,
} from 'lucide-react';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatDate, formatDateTime, isDateInRange } from '@/utils/date';
import { DateFilter } from '@/components/DateFilter';
import type { FeedBrief, FeedGroup } from '@/types/api';

const HistoryPage = () => {
  const {
    data: groups,
    isLoading: groupsLoading,
  } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [selectedBriefId, setSelectedBriefId] = useState<number | null>(null);
  const [timeFilterStart, setTimeFilterStart] = useState<string>('');
  const [timeFilterEnd, setTimeFilterEnd] = useState<string>('');

  useEffect(() => {
    if (!groupId && groups && groups.length > 0) {
      setGroupId(groups[0].id);
    }
  }, [groups, groupId]);

  const groupDetailQuery = useApiQuery<FeedGroup>(
    queryKeys.groupDetail(groupId ?? -1),
    () => api.getGroupDetail(groupId ?? -1),
    {
      enabled: Boolean(groupId),
    },
  );

  const {
    data: historyBriefs,
    isLoading: historyLoading,
  } = useApiQuery<FeedBrief[]>(
    queryKeys.historyBrief(groupId ?? -1),
    () => api.getHistoryBriefByGroup(groupId ?? -1),
    {
      enabled: Boolean(groupId),
    },
  );

  // Filter history briefs by time
  const filteredHistoryBriefs = useMemo(() => {
    if (!historyBriefs) return [];
    if (!timeFilterStart && !timeFilterEnd) {
      return historyBriefs;
    }

    const startDate = timeFilterStart || undefined;
    const endDate = timeFilterEnd || undefined;

    return historyBriefs.filter((brief) =>
      isDateInRange(brief.pubDate, startDate, endDate)
    );
  }, [historyBriefs, timeFilterStart, timeFilterEnd]);

  useEffect(() => {
    setSelectedBriefId(null);
  }, [groupId]);

  const selectedBrief = useMemo(() => {
    if (!selectedBriefId) {
      return null;
    }
    return filteredHistoryBriefs?.find((brief: FeedBrief) => brief.id === selectedBriefId) ?? null;
  }, [selectedBriefId, filteredHistoryBriefs]);

  const selectedGroup: FeedGroup | undefined = useMemo(() => {
    if (groupDetailQuery.data) {
      return groupDetailQuery.data;
    }
    return groups?.find((g: FeedGroup) => g.id === groupId);
  }, [groupDetailQuery.data, groups, groupId]);

  const noGroups = !groupsLoading && (!groups || groups.length === 0);

  if (noGroups || !groupId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-10 text-center animate-in fade-in slide-in-from-top-10 duration-1000">
        <div className="text-slate-500 text-lg italic">
          暂无分组，请先创建分组
        </div>
      </div>
    );
  }

  // Show selected brief detail view
  if (selectedBrief) {
    return (
      <div className="flex flex-col h-full animate-in fade-in slide-in-from-right-8 duration-500">
        <button
          onClick={() => setSelectedBriefId(null)}
          className="mb-6 flex items-center gap-2 text-slate-500 hover:text-white transition-all font-mono text-xs uppercase tracking-widest"
        >
          <ChevronRight size={16} className="rotate-180" /> 返回归档
        </button>
        <div className="flex-1 bg-gradient-to-br from-[#0a0f1d] to-black border border-white/10 rounded-[3rem] shadow-2xl overflow-hidden flex flex-col min-h-0">
          <div className="p-8 border-b border-white/5 bg-slate-900/40 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-black text-white italic tracking-tighter uppercase mb-2 leading-none">
                报告_{selectedBrief.id}
              </h2>
              {selectedGroup && (
                <div className="flex gap-2 mt-2">
                  <span className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded text-[9px] font-black uppercase">
                    {selectedGroup.title}
                  </span>
                </div>
              )}
            </div>
            <span className="text-[10px] font-mono text-slate-600">{formatDateTime(selectedBrief.pubDate)}</span>
          </div>
          <div className="flex-1 overflow-y-auto p-10 custom-scrollbar prose prose-invert prose-cyan max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedBrief.content}</ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  // Show history list view
  return (
    <div className="flex flex-col h-full animate-in fade-in duration-700">
      <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase border-b border-white/5 pb-8 mb-8 italic leading-none">
        历史简报
      </h2>
      <div className="mb-6">
        <DateFilter
          startDate={timeFilterStart}
          endDate={timeFilterEnd}
          onStartDateChange={setTimeFilterStart}
          onEndDateChange={setTimeFilterEnd}
        />
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-10">
        {historyLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-slate-500 text-sm">加载中...</div>
          </div>
        ) : filteredHistoryBriefs.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-slate-500 text-sm italic">所选时间段内未找到简报</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredHistoryBriefs.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedBriefId(item.id)}
                className="group bg-slate-900/30 border border-white/5 rounded-[2rem] p-6 hover:border-indigo-500/30 transition-all cursor-pointer flex items-center justify-between relative"
              >
                <div className="flex items-center gap-6">
                  <div className="p-4 bg-black border border-white/10 rounded-2xl text-indigo-400 group-hover:text-indigo-300 transition-all">
                    <FileText size={24} />
                  </div>
                  <div>
                    <span className="text-[9px] font-mono text-slate-700 block mb-1">
                      {formatDate(item.pubDate)}
                    </span>
                    <h3 className="text-lg font-black text-white italic group-hover:text-indigo-300 transition-colors uppercase">
                      报告_{item.id} · {item.group?.feeds.length || 0} 节点
                    </h3>
                    <p className="text-[10px] text-slate-500 font-light truncate max-w-lg italic">
                      &quot;{item.content.slice(0, 80) || '无内容'}...&quot;
                    </p>
                  </div>
                </div>
                <ArrowRight size={20} className="text-slate-800 group-hover:text-indigo-400 transition-all" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;

