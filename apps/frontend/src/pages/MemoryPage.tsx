import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '@/api/client';
import { Layout } from '@/components/Layout';
import { useToast } from '@/context/ToastContext';
import type { Memory } from '@/types/api';
import { formatDate } from '@/utils/date';

const MemoryPage = () => {
  const { id: memoryIdParam } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [memory, setMemory] = useState<Memory | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (memoryIdParam) {
      const memoryId = parseInt(memoryIdParam, 10);
      if (!isNaN(memoryId)) {
        setIsLoading(true);
        api.getMemory(memoryId)
          .then((data) => {
            setMemory(data);
            setIsLoading(false);
          })
          .catch((error: any) => {
            console.error('Failed to load memory:', error);
            const errorMessage = error?.response?.data?.detail || 
                                error?.response?.data?.message || 
                                error?.message || 
                                '加载历史记忆失败';
            showToast(errorMessage, { type: 'error' });
            setIsLoading(false);
            // 延迟导航，让用户看到错误提示
            setTimeout(() => {
              navigate('/', { replace: true });
            }, 1500);
          });
      } else {
        showToast('无效的历史记忆ID', { type: 'error' });
        navigate('/', { replace: true });
      }
    }
  }, [memoryIdParam, navigate, showToast]);

  const handleBackClick = () => {
    navigate(-1); // 返回上一页
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center">
          <div className="text-slate-400 text-sm">加载中...</div>
        </div>
      </Layout>
    );
  }

  if (!memory) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center">
          <div className="text-slate-400 text-sm">历史记忆不存在</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout showBackButton onBackClick={handleBackClick}>
      <div className="h-full p-2 md:p-4 flex items-center justify-center bg-slate-100/30">
        <div className="w-full max-w-4xl h-full flex flex-col bg-white shadow-2xl rounded-sm overflow-hidden">
          {/* Header */}
          <div className="p-4 md:p-12 pb-4 md:pb-6 border-b border-black/5 shrink-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-indigo-600 rounded-xl md:rounded-2xl flex items-center justify-center text-white shadow-lg shadow-indigo-100">
                    <FileText size={20} className="md:w-6 md:h-6" />
                  </div>
                  <div>
                    <h1 className="text-xl md:text-2xl font-black text-slate-800">
                      历史记忆
                    </h1>
                    <div className="flex items-center gap-2 text-xs md:text-sm text-slate-400 mt-1">
                      <Clock size={14} />
                      <span>{formatDate(memory.created_at)}</span>
                    </div>
                  </div>
                </div>
                <h2 className="text-lg md:text-xl font-bold text-slate-700 mb-2">
                  {memory.topic}
                </h2>
                {memory.reasoning && (
                  <p className="text-sm md:text-base text-slate-600 italic">
                    {memory.reasoning}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-4 md:px-12 py-6 md:py-10 text-sm md:text-base leading-[2.0] text-slate-700 font-medium custom-scrollbar prose prose-slate max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {memory.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default MemoryPage;
