import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import type { Feed } from '@/types/api';
import { Loader } from '@/components/Loader';
import { EmptyState } from '@/components/EmptyState';

const FeedsPage = () => {
  const queryClient = useQueryClient();
  const feedsQuery = useApiQuery<Feed[]>(queryKeys.feeds, api.getFeeds);
  const feeds = useMemo<Feed[]>(() => feedsQuery.data ?? [], [feedsQuery.data]);

  const [selectedFeedId, setSelectedFeedId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editUrl, setEditUrl] = useState('');
  const [editDesc, setEditDesc] = useState('');

  useEffect(() => {
    const target = feeds.find((feed) => feed.id === selectedFeedId);
    if (target) {
      setEditTitle(target.title);
      setEditUrl(target.url);
      setEditDesc(target.desc);
    } else {
      setEditTitle('');
      setEditUrl('');
      setEditDesc('');
    }
  }, [selectedFeedId, feeds]);

  const updateMutation = useApiMutation(async () => {
    if (!selectedFeedId) {
      return;
    }
    await api.updateFeed(selectedFeedId, {
      title: editTitle,
      url: editUrl,
      desc: editDesc,
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
    },
  });

  const deleteMutation = useApiMutation(async (feedId: number) => {
    await api.deleteFeed(feedId);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
      setSelectedFeedId(null);
    },
  });

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const openCreateModal = () => {
    setNewTitle('');
    setNewUrl('');
    setNewDesc('');
    setIsCreateOpen(true);
  };

  const closeCreateModal = () => {
    setIsCreateOpen(false);
  };

  const createMutation = useApiMutation(async () => {
    await api.createFeed({ title: newTitle, url: newUrl, desc: newDesc });
  }, {
    onSuccess: () => {
      setNewTitle('');
      setNewUrl('');
      setNewDesc('');
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
      closeCreateModal();
    },
  });

  const [opmlUrl, setOpmlUrl] = useState('');
  const [opmlContent, setOpmlContent] = useState('');
  const [opmlFileName, setOpmlFileName] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const openImportModal = () => {
    setOpmlUrl('');
    setOpmlContent('');
    setOpmlFileName('');
    setIsImportOpen(true);
  };

  const closeImportModal = () => {
    setIsImportOpen(false);
  };

  const importMutation = useApiMutation(async () => {
    await api.importFeeds({
      url: opmlUrl.trim() || undefined,
      content: opmlContent.trim() || undefined,
    });
  }, {
    onSuccess: () => {
      setOpmlUrl('');
      setOpmlContent('');
      setOpmlFileName('');
      queryClient.invalidateQueries({ queryKey: queryKeys.feeds });
      closeImportModal();
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

  const handleImportSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    importMutation.mutate();
  };

  const handleOpmlFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result === 'string') {
        setOpmlContent(result);
        setOpmlFileName(file.name);
        setOpmlUrl('');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  return (
    <div className="page page-fill feeds-page">
      <header className="main-header">
        <div>
          <h1>Feeds</h1>
          <p className="muted">Manage the RSS sources used to build your daily briefings.</p>
        </div>
        <div className="page-actions">
          <button type="button" className="button secondary" onClick={openImportModal}>
            Import OPML
          </button>
          <button type="button" className="button" onClick={openCreateModal}>
            New feed
          </button>
        </div>
      </header>

      <div className="split-layout feeds-layout">
        <section className="card card-scroll">
          <div className="card-header">
            <h3 className="section-title">All feeds</h3>
          </div>
          <div className="card-body-scroll">
            {feedsQuery.isLoading ? (
              <div className="card-placeholder">
                <Loader label="Loading feeds" />
              </div>
            ) : feeds.length === 0 ? (
              <div className="card-placeholder">
                <EmptyState
                  title="No feeds yet"
                  description="Add feeds manually or import an OPML list to get started."
                />
              </div>
            ) : (
              <div className="table-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>URL</th>
                      <th>Description</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {feeds.map((feed: Feed) => (
                      <tr key={feed.id}>
                        <td>{feed.title}</td>
                        <td>
                          <a href={feed.url} target="_blank" rel="noreferrer">
                            {feed.url}
                          </a>
                        </td>
                        <td>{feed.desc}</td>
                        <td>
                          <div className="table-actions">
                            <button
                              type="button"
                              className="button secondary"
                              onClick={() => setSelectedFeedId(feed.id)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="button danger"
                              onClick={() => {
                                if (window.confirm('Remove this feed from FlashNews?')) {
                                  deleteMutation.mutate(feed.id);
                                }
                              }}
                              disabled={deleteMutation.isPending}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        <div className="feeds-side">
          <section className="card card-scroll">
            <div className="card-header">
              <h3 className="section-title">Edit feed</h3>
            </div>
            <div className="card-body-scroll">
              {selectedFeedId ? (
                <form className="form-grid" onSubmit={handleUpdateSubmit}>
                  <div className="form-row">
                    <label htmlFor="edit-feed-title">Title</label>
                    <input
                      id="edit-feed-title"
                      className="input"
                      value={editTitle}
                      onChange={(event) => setEditTitle(event.target.value)}
                      required
                    />
                  </div>
                  <div className="form-row">
                    <label htmlFor="edit-feed-url">URL</label>
                    <input
                      id="edit-feed-url"
                      className="input"
                      value={editUrl}
                      onChange={(event) => setEditUrl(event.target.value)}
                      required
                      type="url"
                    />
                  </div>
                  <div className="form-row fill">
                    <label htmlFor="edit-feed-desc">Description</label>
                    <textarea
                      id="edit-feed-desc"
                      className="textarea"
                      value={editDesc}
                      onChange={(event) => setEditDesc(event.target.value)}
                    />
                  </div>
                  <div className="page-actions sticky-actions">
                    <button className="button" type="submit" disabled={updateMutation.isPending}>
                      {updateMutation.isPending ? 'Saving…' : 'Save feed'}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="card-placeholder">
                  <EmptyState
                    title="Select a feed"
                    description="Pick a feed from the table to edit its details."
                  />
                </div>
              )}
            </div>
          </section>
        </div>
      </div>

      {isCreateOpen ? (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={closeCreateModal}>
          <div className="modal-content card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3 className="section-title" style={{ marginBottom: 0 }}>Add feed</h3>
              <button type="button" className="modal-close" aria-label="Close" onClick={closeCreateModal}>
                ×
              </button>
            </div>
            <form className="form-grid modal-body" onSubmit={handleCreateSubmit}>
              <div className="form-row">
                <label htmlFor="new-feed-title">Title</label>
                <input
                  id="new-feed-title"
                  className="input"
                  value={newTitle}
                  onChange={(event) => setNewTitle(event.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label htmlFor="new-feed-url">URL</label>
                <input
                  id="new-feed-url"
                  className="input"
                  value={newUrl}
                  onChange={(event) => setNewUrl(event.target.value)}
                  required
                  type="url"
                />
              </div>
              <div className="form-row">
                <label htmlFor="new-feed-desc">Description</label>
                <textarea
                  id="new-feed-desc"
                  className="textarea"
                  value={newDesc}
                  onChange={(event) => setNewDesc(event.target.value)}
                />
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
                  {createMutation.isPending ? 'Creating…' : 'Create feed'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {isImportOpen ? (
        <div className="modal-overlay" role="dialog" aria-modal="true" onClick={closeImportModal}>
          <div className="modal-content card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3 className="section-title" style={{ marginBottom: 0 }}>Import feeds</h3>
              <button type="button" className="modal-close" aria-label="Close" onClick={closeImportModal}>
                ×
              </button>
            </div>
            <form className="form-grid modal-body" onSubmit={handleImportSubmit}>
              <div className="form-row">
                <label htmlFor="opml-url">OPML file URL</label>
                <input
                  id="opml-url"
                  className="input"
                  value={opmlUrl}
                  onChange={(event) => setOpmlUrl(event.target.value)}
                  placeholder="https://example.com/subscriptions.opml"
                  type="url"
                />
              </div>
              <div className="form-row">
                <label htmlFor="opml-content">OPML content</label>
                <textarea
                  id="opml-content"
                  className="textarea"
                  value={opmlContent}
                  onChange={(event) => setOpmlContent(event.target.value)}
                  placeholder="Paste OPML XML here"
                />
              </div>
              <div className="form-row">
                <label>Upload file</label>
                <div className="modal-upload">
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Choose OPML file
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".opml,.xml,text/xml"
                    style={{ display: 'none' }}
                    onChange={handleOpmlFileSelect}
                  />
                  {opmlFileName ? (
                    <span className="muted" style={{ fontSize: '0.85rem' }}>
                      {opmlFileName}
                    </span>
                  ) : (
                    <span className="muted" style={{ fontSize: '0.85rem' }}>
                      No file selected
                    </span>
                  )}
                </div>
              </div>
              <p className="muted" style={{ marginBottom: 0 }}>
                Provide a URL, paste the content, or upload an OPML file. Existing feeds with the same URL
                will be skipped.
              </p>
              <div className="modal-actions">
                <button
                  type="button"
                  className="button secondary"
                  onClick={closeImportModal}
                  disabled={importMutation.isPending}
                >
                  Cancel
                </button>
                <button className="button" type="submit" disabled={importMutation.isPending}>
                  {importMutation.isPending ? 'Importing…' : 'Import feeds'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default FeedsPage;
