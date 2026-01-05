import { FormEvent, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Save, Check, Key, Server } from 'lucide-react';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import type { Setting } from '@/types/api';
import { useToast } from '@/context/ToastContext';

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Gemini' },
];

const SettingsPage = () => {
  const queryClient = useQueryClient();
  const { data: setting, isLoading } = useApiQuery<Setting>(queryKeys.setting, api.getSetting);
  const { showToast } = useToast();

  const [modelId, setModelId] = useState('');
  const [provider, setProvider] = useState('openai');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    if (setting) {
      setModelId(setting.model.model);
      setProvider(setting.model.provider);
      setBaseUrl(setting.model.baseUrl ?? '');
      setApiKey('');
    }
  }, [setting]);

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
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
      showToast('模型配置已保存');
    },
    onError: (error) => {
      showToast(error.message || '更新模型配置失败', { type: 'error' });
    },
  });

  const handleModelSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    modelMutation.mutate();
  };

  if (isLoading || !setting) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-500 text-sm">加载设置中...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-700 min-h-0 max-w-4xl mx-auto w-full justify-center">
      <div className="flex-shrink-0 flex justify-between items-end border-b border-white/5 pb-4 mb-8">
        <div>
          <h2 className="text-2xl font-black text-white italic tracking-tighter uppercase leading-none italic">
            系统配置
          </h2>
        </div>
        <button
          onClick={() => {
            modelMutation.mutate();
          }}
          className={`px-6 py-2 rounded-xl font-black flex items-center gap-2 uppercase text-[9px] tracking-widest shadow-xl transition-all ${
            isSaved ? 'bg-green-500 text-white' : 'bg-white text-black hover:bg-cyan-400'
          }`}
          disabled={modelMutation.isPending}
        >
          {isSaved ? <Check size={14} /> : <Save size={14} />}{' '}
          {isSaved ? '已同步' : '应用配置'}
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 shadow-inner flex flex-col justify-center overflow-hidden">
          <h4 className="text-[16px] font-black text-cyan-400 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full shadow-[0_0_8px_cyan]"></div>
            Provider
          </h4>
          <div className="flex gap-2 bg-black/40 p-1 rounded-xl border border-white/5">
            {providerOptions.map((p) => (
              <button
                key={p.value}
                onClick={() => setProvider(p.value)}
                className={`flex-1 py-2.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                  provider === p.value
                    ? 'bg-white text-black shadow-lg'
                    : 'text-slate-500 hover:text-white'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 flex flex-col justify-center">
          <h4 className="text-[16px] font-black text-purple-400 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-purple-500 rounded-full shadow-[0_0_8px_purple]"></div>
            Model
          </h4>
          <input
            type="text"
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
            placeholder="模型 ID..."
            className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono text-[14px] outline-none focus:border-purple-500 transition-all"
          />
        </div>
        <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 flex flex-col justify-center md:col-span-2">
          <h4 className="text-[16px] font-black text-amber-400 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-amber-500 rounded-full shadow-[0_0_8px_amber]"></div>
            API Key
          </h4>
          <div className="relative">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="输入 API Key..."
              className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono text-[14px] outline-none focus:border-amber-500 transition-all tracking-[0.2em] pr-10"
            />
            <Key size={12} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-700" />
          </div>
        </div>
        <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 flex flex-col justify-center md:col-span-2">
          <h4 className="text-[16px] font-black text-blue-400 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full shadow-[0_0_8px_blue]"></div>
            Base URL
          </h4>
          <div className="relative">
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.endpoint..."
              className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono text-[14px] outline-none focus:border-blue-500 transition-all pr-10"
            />
            <Server size={12} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-700" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
