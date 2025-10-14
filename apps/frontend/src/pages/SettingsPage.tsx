import { FormEvent, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import { Loader } from '@/components/Loader';
import type { Setting } from '@/types/api';
import { useToast } from '@/context/ToastContext';

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Google Gemini' },
];

const SettingsPage = () => {
  const queryClient = useQueryClient();
  const { data: setting, isLoading } = useApiQuery<Setting>(queryKeys.setting, api.getSetting);
  const { showToast } = useToast();

  const [prompt, setPrompt] = useState('');
  const [briefTime, setBriefTime] = useState('08:00');
  const [modelId, setModelId] = useState('');
  const [provider, setProvider] = useState('openai');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');

  useEffect(() => {
    if (setting) {
      setPrompt(setting.prompt);
      setBriefTime(setting.briefTime ?? '08:00');
      setModelId(setting.model.model);
      setProvider(setting.model.provider);
      setBaseUrl(setting.model.baseUrl ?? '');
      setApiKey('');
    }
  }, [setting]);

  const promptMutation = useApiMutation(async (nextPrompt: string) => {
    await api.updateSetting({ prompt: nextPrompt });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.setting });
      showToast('Prompt updated successfully.');
    },
    onError: (error) => {
      showToast(error.message || 'Failed to update prompt.', { type: 'error' });
    },
  });

  const modelMutation = useApiMutation(async () => {
    await api.updateSetting({
      model: {
        model: modelId,
        provider,
        apiKey,
        baseUrl: baseUrl || undefined,
      },
    });
  }, {
    onSuccess: () => {
      setApiKey('');
      queryClient.invalidateQueries({ queryKey: queryKeys.setting });
      showToast('Model configuration saved.');
    },
    onError: (error) => {
      showToast(error.message || 'Failed to update model configuration.', { type: 'error' });
    },
  });

  const briefTimeMutation = useApiMutation(async (nextBriefTime: string) => {
    await api.updateBriefTime(nextBriefTime);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.setting });
      showToast('Schedule updated successfully.');
    },
    onError: (error) => {
      showToast(error.message || 'Failed to update schedule.', { type: 'error' });
    },
  });

  const handlePromptSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    promptMutation.mutate(prompt);
  };

  const handleModelSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    modelMutation.mutate();
  };

  const handleBriefTimeSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    briefTimeMutation.mutate(briefTime);
  };

  return (
    <div className="page page-fill settings-page">
      <header className="main-header">
        <div>
          <h1>LLM Settings</h1>
          <p className="muted">Control the schedule, prompt, and model used for generating summaries.</p>
        </div>
      </header>

      {isLoading || !setting ? (
        <section className="card card-scroll">
          <div className="card-body-scroll">
            <Loader label="Loading settings" />
          </div>
        </section>
      ) : (
        <div className="settings-layout">
          <section className="card card-scroll">
            <div className="card-header">
              <h3 className="section-title">Brief generation</h3>
            </div>
            <div className="card-body-scroll">
              <div className="card-section">
                <form className="form-grid brief-time-form" onSubmit={handleBriefTimeSubmit}>
                  <div className="form-row">
                    <label htmlFor="brief-time">Daily brief time</label>
                    <input
                      id="brief-time"
                      className="input"
                      type="time"
                      step={60}
                      value={briefTime}
                      onChange={(event) => setBriefTime(event.target.value)}
                      required
                    />
                  </div>
                  <p className="muted form-help">
                    Choose when NewsCollector should generate the daily brief. Times use 24-hour format and the
                    server time zone.
                  </p>
                  <div className="page-actions sticky-actions">
                    <button className="button" type="submit" disabled={briefTimeMutation.isPending}>
                      {briefTimeMutation.isPending ? 'Saving…' : 'Update schedule'}
                    </button>
                  </div>
                </form>
              </div>
              <hr className="card-divider" />
              <div className="card-section">
                <form className="form-grid prompt-form" onSubmit={handlePromptSubmit}>
                  <div className="form-row fill">
                    <label htmlFor="prompt">Prompt</label>
                    <textarea
                      id="prompt"
                      className="textarea"
                      value={prompt}
                      onChange={(event) => setPrompt(event.target.value)}
                      required
                    />
                  </div>
                  <p className="muted form-help">
                    The prompt guides how the LLM summarizes daily content. Adjust instructions if you need
                    shorter headlines, detailed overviews, or a different tone.
                  </p>
                  <div className="page-actions sticky-actions">
                    <button className="button" type="submit" disabled={promptMutation.isPending}>
                      {promptMutation.isPending ? 'Saving…' : 'Update prompt'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </section>

          <section className="card card-scroll">
            <div className="card-header">
              <h3 className="section-title">Model configuration</h3>
            </div>
            <div className="card-body-scroll">
              <form className="form-grid model-form" onSubmit={handleModelSubmit}>
                <div className="form-row">
                  <label htmlFor="model-id">Model ID</label>
                  <input
                    id="model-id"
                    className="input"
                    value={modelId}
                    onChange={(event) => setModelId(event.target.value)}
                    placeholder="The identifier expected by the provider"
                    required
                  />
                </div>

                <div className="form-row two-column">
                  <div className="form-field">
                    <label htmlFor="provider">Provider</label>
                    <select
                      id="provider"
                      className="select"
                      value={provider}
                      onChange={(event) => setProvider(event.target.value)}
                      required
                    >
                      {providerOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-field">
                    <label htmlFor="base-url">Base URL</label>
                    <input
                      id="base-url"
                      className="input"
                      value={baseUrl}
                      onChange={(event) => setBaseUrl(event.target.value)}
                      placeholder="https://api.provider.com"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <label htmlFor="api-key">API key</label>
                  <input
                    id="api-key"
                    className="input"
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                    placeholder="Paste a new key to update"
                    required
                    type="password"
                  />
                </div>

                <p className="muted form-help">
                  The existing API key is hidden. Provide the key again whenever you update the model settings.
                </p>

                <div className="page-actions sticky-actions">
                  <button className="button" type="submit" disabled={modelMutation.isPending}>
                    {modelMutation.isPending ? 'Saving…' : 'Update model'}
                  </button>
                </div>
              </form>
            </div>
          </section>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
