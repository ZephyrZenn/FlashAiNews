import { useEffect, useRef } from 'react';
import { api } from '@/api/client';

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  logs: Array<{ text: string; time: string }>;
  result?: string;
  error?: string;
}

interface UseTaskPollingOptions {
  taskId: string | null;
  onLogUpdate?: (logs: TaskStatus['logs']) => void;
  onComplete?: (result: string) => void;
  onError?: (error: string) => void;
  interval?: number; // 轮询间隔（毫秒），默认3000ms
  enabled?: boolean; // 是否启用轮询
}

export const useTaskPolling = ({
  taskId,
  onLogUpdate,
  onComplete,
  onError,
  interval = 3000,
  enabled = true,
}: UseTaskPollingOptions) => {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastLogCountRef = useRef(0);

  useEffect(() => {
    if (!taskId || !enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const poll = async () => {
      try {
        const status = await api.getBriefGenerationStatus(taskId);
        
        // 检查是否有新日志
        if (status.logs.length > lastLogCountRef.current) {
          onLogUpdate?.(status.logs);
          lastLogCountRef.current = status.logs.length;
        }

        // 检查任务状态
        if (status.status === 'completed') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onComplete?.(status.result || '');
        } else if (status.status === 'failed') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onError?.(status.error || '任务执行失败');
        }
        // 如果状态是 pending 或 running，继续轮询
      } catch (error: any) {
        console.error('Polling error:', error);
        // 如果是 404 错误（任务不存在），停止轮询
        if (error?.response?.status === 404) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onError?.('任务不存在或已被清理');
        }
        // 其他错误继续轮询，但记录日志
      }
    };

    // 立即执行一次
    poll();
    
    // 设置轮询
    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [taskId, enabled, interval, onLogUpdate, onComplete, onError]);
};
