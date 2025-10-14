import { useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import { Loader } from '@/components/Loader';
import { EmptyState } from '@/components/EmptyState';
import { useToast } from '@/context/ToastContext';
import { formatDate, formatDateTime } from '@/utils/date';
import type { FeedBrief, FeedGroup } from '@/types/api';

const SummaryPage = () => {
  const {
    data: groups,
    isLoading: groupsLoading,
  } = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const [groupId, setGroupId] = useState<number | null>(null);

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
    data: todayBrief,
    isLoading: todayLoading,
    refetch: refetchToday,
  } = useApiQuery<FeedBrief | null>(
    queryKeys.todayBrief(groupId ?? -1),
    () => api.getTodayBriefByGroup(groupId ?? -1),
    {
      enabled: Boolean(groupId),
    },
  );

  const {
    data: historyBriefs,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useApiQuery<FeedBrief[]>(
    queryKeys.historyBrief(groupId ?? -1),
    () => api.getHistoryBriefByGroup(groupId ?? -1),
    {
      enabled: Boolean(groupId),
    },
  );

  const [selectedBriefId, setSelectedBriefId] = useState<number | null>(null);
  const { showToast } = useToast();

  const generateMutation = useApiMutation(async () => {
    await api.generateTodayBrief();
  }, {
    onSuccess: () => {
      showToast('Started generating today\'s brief.');
      refetchToday();
      refetchHistory();
    },
    onError: (error) => {
      showToast(error.message || 'Failed to start brief generation.', { type: 'error' });
    },
  });

  useEffect(() => {
    setSelectedBriefId(null);
  }, [groupId]);

  useEffect(() => {
    if (!groupId) {
      return;
    }
    if (todayBrief && todayBrief.content.trim()) {
      setSelectedBriefId(todayBrief.id);
      return;
    }
    if (!todayLoading && historyBriefs && historyBriefs.length > 0) {
      setSelectedBriefId(historyBriefs[0].id);
    }
  }, [groupId, todayBrief, todayLoading, historyBriefs]);

  const selectedBrief = useMemo(() => {
    if (!selectedBriefId) {
      return null;
    }
    if (todayBrief && todayBrief.id === selectedBriefId) {
      return todayBrief;
    }
    return historyBriefs?.find((brief: FeedBrief) => brief.id === selectedBriefId) ?? null;
  }, [selectedBriefId, todayBrief, historyBriefs]);

  const selectedGroup: FeedGroup | undefined = useMemo(() => {
    if (groupDetailQuery.data) {
      return groupDetailQuery.data;
    }
    return groups?.find((g: FeedGroup) => g.id === groupId);
  }, [groupDetailQuery.data, groups, groupId]);

  const noGroups = !groupsLoading && (!groups || groups.length === 0);
  const isEmpty = !todayLoading && !historyLoading && !selectedBrief?.content?.trim();
  const handleGenerateClick = () => {
    if (generateMutation.isPending || !groupId) {
      return;
    }
    generateMutation.mutate();
  };

  return (
    <div className="page page-fill summary-page">
      <header className="main-header">
        <div>
          <h1>Daily Briefings</h1>
          <p className="muted">Summaries generated from your feed groups and LLM configuration.</p>
        </div>
        <div className="page-actions">
          <button
            className="button"
            type="button"
            onClick={handleGenerateClick}
            disabled={
              generateMutation.isPending
              || todayLoading
              || !groupId
              || groupsLoading
            }
          >
            {generateMutation.isPending ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </header>

      <div className="summary-layout">
        <section className="card card-scroll">
          <div className="card-header summary-header">
            <div>
              <h2 className="card-title">Today&apos;s Overview</h2>
              <p className="card-subtitle">
                {selectedGroup ? `Group: ${selectedGroup.title}` : 'Select a group to inspect its summary.'}
              </p>
            </div>
            <div className="summary-controls">
              {groupsLoading ? (
                <Loader label="Loading groups" />
              ) : groups && groups.length > 0 ? (
                <>
                  <select
                    className="select"
                    value={groupId ?? ''}
                    onChange={(event) => setGroupId(Number(event.target.value))}
                  >
                    {groups.map((group: FeedGroup) => (
                      <option key={group.id} value={group.id}>
                        {group.title}
                      </option>
                    ))}
                  </select>
                  <button
                    className="button secondary"
                    type="button"
                    onClick={() => refetchToday()}
                    disabled={todayLoading || generateMutation.isPending || !groupId}
                  >
                    Refresh
                  </button>
                </>
              ) : null}
            </div>
          </div>

          <div className="card-body-scroll">
            {noGroups ? (
              <div className="card-placeholder">
                <EmptyState
                  title="No groups configured"
                  description="Create a feed group to generate a daily summary."
                />
              </div>
            ) : todayLoading && !selectedBrief ? (
              <div className="card-placeholder">
                <Loader label="Fetching today&apos;s summary" />
              </div>
            ) : isEmpty ? (
              <div className="card-placeholder">
                <EmptyState
                  title="No summary yet"
                  description="Your feeds may still be processing. Come back later or adjust your feed groups."
                />
              </div>
            ) : selectedBrief ? (
              <>
                <div className="chip">
                  {selectedBrief.id === todayBrief?.id ? 'Today' : 'Historical'}
                  <span>· {formatDateTime(selectedBrief.pubDate)}</span>
                </div>
                {selectedGroup?.desc ? (
                  <p className="muted" style={{ margin: '0 0 0.75rem 0' }}>
                    {selectedGroup.desc}
                  </p>
                ) : null}
                <article className="summary-content summary-article">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedBrief.content}</ReactMarkdown>
                </article>
              </>
            ) : null}
          </div>
        </section>

        <aside className="summary-side">
          <div className="card card-scroll">
            <div className="card-header">
              <h3 className="section-title">Brief History</h3>
            </div>
            <div className="card-body-scroll">
              {noGroups ? (
                <div className="card-placeholder">
                  <p className="muted">Create a group to start tracking historical summaries.</p>
                </div>
              ) : historyLoading ? (
                <div className="card-placeholder">
                  <Loader label="Loading history" />
                </div>
              ) : historyBriefs && historyBriefs.length > 0 ? (
                <div className="history-list">
                  {historyBriefs.map((brief: FeedBrief) => (
                    <button
                      type="button"
                      key={brief.id}
                      className={`history-item${selectedBriefId === brief.id ? ' active' : ''}`}
                      onClick={() => setSelectedBriefId(brief.id)}
                    >
                      <div>{formatDate(brief.pubDate)}</div>
                      <div className="muted" style={{ fontSize: '0.85rem' }}>
                        {brief.content.slice(0, 96) || 'No summary stored for this date.'}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="card-placeholder">
                  <p className="muted">No historical summaries yet for this group.</p>
                </div>
              )}
            </div>
          </div>

          <div className="card card-scroll">
            <div className="card-header">
              <h3 className="section-title">Group Feeds</h3>
            </div>
            <div className="card-body-scroll">
              {noGroups ? (
                <div className="card-placeholder">
                  <p className="muted">Create a group to connect feeds.</p>
                </div>
              ) : groupDetailQuery.isLoading ? (
                <div className="card-placeholder">
                  <Loader label="Loading feeds" />
                </div>
              ) : selectedGroup ? (
                selectedGroup.feeds.length > 0 ? (
                  <div className="feed-chip-list">
                    {selectedGroup.feeds.map((feed) => (
                      <span key={feed.id} className="feed-chip">
                        {feed.title}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="card-placeholder">
                    <p className="muted">No feeds connected to this group.</p>
                  </div>
                )
              ) : (
                <div className="card-placeholder">
                  <p className="muted">Choose a group to view its feeds.</p>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default SummaryPage;
