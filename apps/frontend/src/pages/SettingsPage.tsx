import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Settings,
  Cpu,
  Globe,
  Database,
  Save,
  Check,
} from 'lucide-react';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { useApiMutation } from '@/hooks/useApiMutation';
import { Layout } from '@/components/Layout';
import { useToast } from '@/context/ToastContext';
import { Select } from '@/components/ui/Select';
import type { Setting } from '@/types/api';

const SettingsPage = () => {
  const queryClient = useQueryClient();
  const { data: setting } = useApiQuery<Setting>(queryKeys.settings, api.getSetting);
  const { showToast } = useToast();

  const [systemConfig, setSystemConfig] = useState({
    modelName: 'gpt-4o-mini',
    provider: 'openai',
    baseUrl: '',
  });
  const [showSaveToast, setShowSaveToast] = useState(false);

  // Load settings from API
  useEffect(() => {
    if (setting) {
      setSystemConfig({
        modelName: setting.model.model || 'gpt-4o-mini',
        provider: setting.model.provider || 'openai',
        baseUrl: setting.model.baseUrl || '',
      });
    }
  }, [setting]);

  const saveMutation = useApiMutation(async () => {
    await api.updateSetting({
      model: {
        model: systemConfig.modelName,
        provider: systemConfig.provider,
        // Only send baseUrl for 'other' provider
        baseUrl: systemConfig.provider === 'other' ? systemConfig.baseUrl : undefined,
      },
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings });
      setShowSaveToast(true);
      setTimeout(() => setShowSaveToast(false), 3000);
      showToast('配置保存成功');
    },
    onError: (error) => {
      showToast(error.message || '保存配置失败', { type: 'error' });
    },
  });

  const handleSaveConfig = () => {
    saveMutation.mutate();
  };

  return (
    <Layout>
      {/* Settings view - exactly matching t.tsx settings tab */}
      <div className="h-full overflow-hidden p-8 flex justify-center items-center">
        <div className="w-full max-w-2xl bg-white rounded-[2.5rem] border border-slate-100 p-8 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6 pb-4 border-b border-slate-50">
            <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center text-indigo-600">
              <Settings size={24} />
            </div>
            <div>
              <h3 className="text-xl font-black text-slate-800 tracking-tight">
                模型配置
              </h3>
              <p className="text-slate-400 text-xs font-medium tracking-wide uppercase">
                Core AI Configuration
              </p>
            </div>
          </div>

          {/* Form Fields */}
          <div className="space-y-6">
            {/* Model Name */}
            <div>
              <div className="flex items-center gap-2 mb-2 ml-1">
                <Cpu size={14} className="text-indigo-500" />
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                  Model 名称
                </label>
              </div>
              <input
                type="text"
                value={systemConfig.modelName}
                onChange={(e) =>
                  setSystemConfig({ ...systemConfig, modelName: e.target.value })
                }
                className="w-full bg-slate-50 border-none rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all font-medium text-slate-700"
              />
            </div>

            {/* Provider */}
            <div>
              <div className="flex items-center gap-2 mb-2 ml-1">
                <Globe size={14} className="text-indigo-500" />
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                  提供商 (Provider)
                </label>
              </div>
              <Select
                value={systemConfig.provider}
                onChange={(value) =>
                  setSystemConfig({ ...systemConfig, provider: value })
                }
                options={[
                  { value: 'openai', label: 'OpenAI' },
                  { value: 'deepseek', label: 'Deepseek' },
                  { value: 'gemini', label: 'Gemini' },
                  { value: 'other', label: 'Other (OpenAI Compatible)' },
                ]}
              />
              <p className="text-xs text-slate-400 mt-2 ml-1">
                API Key 需在环境变量中配置: OPENAI_API_KEY / DEEPSEEK_API_KEY / GEMINI_API_KEY / MODEL_API_KEY
              </p>
            </div>

            {/* Base URL - Only show for 'other' provider */}
            {systemConfig.provider === 'other' && (
              <div>
                <div className="flex items-center gap-2 mb-2 ml-1">
                  <Database size={14} className="text-indigo-500" />
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Base URL
                  </label>
                </div>
                <input
                  type="text"
                  value={systemConfig.baseUrl}
                  onChange={(e) =>
                    setSystemConfig({ ...systemConfig, baseUrl: e.target.value })
                  }
                  placeholder="https://your-api-provider.com/v1"
                  className="w-full bg-slate-50 border-none rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all font-mono text-slate-500"
                />
                <p className="text-xs text-slate-400 mt-2 ml-1">
                  请输入 OpenAI 兼容 API 的 Base URL
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-10 pt-6 border-t border-slate-50 flex items-center justify-between">
            <div
              className={`flex items-center gap-2 text-emerald-500 text-[10px] font-bold transition-all duration-500 ${
                showSaveToast
                  ? 'opacity-100 translate-x-0'
                  : 'opacity-0 -translate-x-4'
              }`}
            >
              <Check size={14} /> 保存成功
            </div>
            <button
              onClick={handleSaveConfig}
              className="flex items-center gap-2 bg-indigo-600 text-white px-10 py-3 rounded-2xl font-black shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all active:scale-95 text-sm uppercase tracking-wider"
            >
              <Save size={18} /> 保存
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default SettingsPage;
