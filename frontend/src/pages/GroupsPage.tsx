import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import type { Feed, FeedGroup } from '@/types/api';
import { Loader } from '@/components/Loader';
import { EmptyState } from '@/components/EmptyState';

const GroupsPage = () => {
  const queryClient = useQueryClient();
  const groupsQuery = useApiQuery<FeedGroup[]>(queryKeys.groups, api.getGroups);
  const feedsQuery = useApiQuery<Feed[]>(queryKeys.feeds, api.getFeeds);

  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);

  useEffect(() => {
    if (!selectedGroupId && groupsQuery.data && groupsQuery.data.length > 0) {
      setSelectedGroupId(groupsQuery.data[0].id);
    }
  }, [groupsQuery.data, selectedGroupId]);

  const groupDetailQuery = useApiQuery<FeedGroup>(
    queryKeys.groupDetail(selectedGroupId ?? -1),
    () => api.getGroupDetail(selectedGroupId ?? -1),
    { enabled: Boolean(selectedGroupId) },
  );

  const selectedGroup = groupDetailQuery.data;

  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editFeedIds, setEditFeedIds] = useState<number[]>([]);

  useEffect(() => {
    if (selectedGroup) {
      setEditTitle(selectedGroup.title);
      setEditDesc(selectedGroup.desc);
      setEditFeedIds(selectedGroup.feeds.map((feed) => feed.id));
    }
  }, [selectedGroup]);

  const toggleFeedSelection = (feedId: number) => {
    setEditFeedIds((prev) =>
      prev.includes(feedId) ? prev.filter((id) => id !== feedId) : [...prev, feedId],
    );
  };

  const updateMutation = useApiMutation(async () => {
    if (!selectedGroupId) {
      return;
    }
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
    },
  });

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newGroupTitle, setNewGroupTitle] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newGroupFeedIds, setNewGroupFeedIds] = useState<number[]>([]);

  const openCreateModal = () => {
    setNewGroupTitle('');
    setNewGroupDesc('');
    setNewGroupFeedIds([]);
    setIsCreateOpen(true);
  };

  const closeCreateModal = () => {
    setIsCreateOpen(false);
  };

  const toggleNewGroupFeed = (feedId: number) => {
    setNewGroupFeedIds((prev) =>
      prev.includes(feedId) ? prev.filter((id) => id !== feedId) : [...prev, feedId],
    );
  };

  const createMutation = useApiMutation(async () => {
    const newId = await api.createGroup({
      title: newGroupTitle,
      desc: newGroupDesc,
      feedIds: newGroupFeedIds,
    });
    return newId;
  }, {
    onSuccess: (gid) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.groups });
      if (gid) {
        setSelectedGroupId(gid);
      }
      closeCreateModal();
    },
  });

  const handleUpdateSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateMutation.mutate();
  };

  const handleCreateSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createMutation.mutate();
  };

  const allFeeds: Feed[] = feedsQuery.data ?? [];
  const orderedGroups = useMemo<FeedGroup[]>(
    () => groupsQuery.data ?? [],
    [groupsQuery.data],
  );

  const renderFeedSelector = (
    selectedIds: number[],
    toggle: (feedId: number) => void,
    emptyCopy: string,
  ) => {
    if (feedsQuery.isLoading) {
      return <Loader label="Loading feeds" />;
    }
    if (allFeeds.length === 0) {
      return <span className="muted">{emptyCopy}</span>;
    }
    return (
      <div className="checkbox-list">
        {allFeeds.map((feed: Feed) => (
          <label key={feed.id} className="checkbox-row">
            <input
              type="checkbox"
              checked={selectedIds.includes(feed.id)}
              onChange={() => toggle(feed.id)}
            />
            <span>{feed.title}</span>
          </label>
        ))}
      </div>
    );
  };

  return (
    <div className="page page-fill groups-page">
      <header className="main-header">
        <div>
          <h1>Groups</h1>
          <p className="muted">Organize feeds into thematic groups for daily summaries.</p>
        </div>
        <button type="button" className="button" onClick={openCreateModal}>
          New group
        </button>
      </header>

      <div className="split-layout groups-layout">
        <section className="card card-scroll">
          <div className="card-header">
            <h3 className="section-title">Feed Groups</h3>
          </div>
          <div className="card-body-scroll">
            {groupsQuery.isLoading ? (
              <div className="card-placeholder">
                <Loader label="Loading groups" />
              </div>
            ) : orderedGroups.length === 0 ? (
              <div className="card-placeholder">
                <EmptyState
                  title="No groups yet"
                  description="Create your first group to start summarizing related feeds together."
                />
              </div>
            ) : (
              <div className="history-list">
              {orderedGroups.map((group: FeedGroup) => (
                  <button
                    type="button"
                    key={group.id}
                    className={`history-item${selectedGroupId === group.id ? ' active' : ''}`}
                    onClick={() => setSelectedGroupId(group.id)}
                  >
                    <div className="history-item-title">{group.title}</div>
                    <div className="muted history-item-subtitle">
                      {group.desc || 'No description provided.'}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="card card-scroll">
          <div className="card-header">
            <h3 className="section-title">Group details</h3>
          </div>
          <div className="card-body-scroll">
            {selectedGroupId && groupDetailQuery.isLoading ? (
              <div className="card-placeholder">
                <Loader label="Loading group" />
              </div>
            ) : selectedGroup ? (
              <form className="form-grid group-form" onSubmit={handleUpdateSubmit}>
                <div className="form-row">
                  <label htmlFor="group-title">Title</label>
                  <input
                    id="group-title"
                    className="input"
                    value={editTitle}
                    onChange={(event) => setEditTitle(event.target.value)}
                    required
                  />
                </div>

                <div className="form-row">
                  <label htmlFor="group-desc">Description</label>
                  <textarea
                    id="group-desc"
                    className="textarea"
                    value={editDesc}
                    onChange={(event) => setEditDesc(event.target.value)}
                    placeholder="Explain what this group covers"
                  />
                </div>

                <div className="form-row fill">
                  <label>Feeds</label>
                  <div className="form-row-content">
                    {renderFeedSelector(
                      editFeedIds,
                      toggleFeedSelection,
                      'No feeds available. Create one first.',
                    )}
                  </div>
                </div>

                <div className="page-actions sticky-actions">
                  <button className="button" type="submit" disabled={updateMutation.isPending}>
                    {updateMutation.isPending ? 'Saving…' : 'Save changes'}
                  </button>
                </div>
              </form>
            ) : orderedGroups.length === 0 ? (
              <div className="card-placeholder">
                <EmptyState
                  title="Create a group"
                  description="Add a group to start editing its details."
                />
              </div>
            ) : (
              <div className="card-placeholder">
                <EmptyState
                  title="Select a group"
                  description="Choose a group from the list to view and edit its details."
                />
              </div>
            )}
          </div>
        </section>
      </div>

      {isCreateOpen ? (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={closeCreateModal}>
          <div
            className="modal-content card"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <h3 className="section-title" style={{ marginBottom: 0 }}>Create group</h3>
              <button type="button" className="modal-close" onClick={closeCreateModal} aria-label="Close">
                ×
              </button>
            </div>
            <form className="form-grid modal-body" onSubmit={handleCreateSubmit}>
              <div className="form-row">
                <label htmlFor="new-group-title">Title</label>
                <input
                  id="new-group-title"
                  className="input"
                  value={newGroupTitle}
                  onChange={(event) => setNewGroupTitle(event.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label htmlFor="new-group-desc">Description</label>
                <textarea
                  id="new-group-desc"
                  className="textarea"
                  value={newGroupDesc}
                  onChange={(event) => setNewGroupDesc(event.target.value)}
                  placeholder="What does this group cover?"
                />
              </div>
              <div className="form-row">
                <label>Feeds</label>
                {renderFeedSelector(
                  newGroupFeedIds,
                  toggleNewGroupFeed,
                  'Add feeds before grouping them.',
                )}
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="button secondary"
                  onClick={closeCreateModal}
                  disabled={createMutation.isPending}
                >
                  Cancel
                </button>
                <button className="button" type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating…' : 'Create group'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default GroupsPage;
