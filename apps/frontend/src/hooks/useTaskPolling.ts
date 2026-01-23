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
  const currentTaskIdRef = useRef<string | null>(null);
  
  // 使用 ref 存储回调函数，避免因回调函数引用变化而重新设置轮询
  const onLogUpdateRef = useRef(onLogUpdate);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  // 更新 ref 的值，确保始终使用最新的回调函数
  useEffect(() => {
    onLogUpdateRef.current = onLogUpdate;
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onLogUpdate, onComplete, onError]);

  useEffect(() => {
    // 清除旧的轮询
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // 如果 taskId 变化，重置日志计数
    if (currentTaskIdRef.current !== taskId) {
      lastLogCountRef.current = 0;
      currentTaskIdRef.current = taskId;
    }

    if (!taskId || !enabled) {
      return;
    }

    const poll = async () => {
      // 使用 ref 中的 taskId，确保使用最新的值
      const currentTaskId = currentTaskIdRef.current;
      if (!currentTaskId) {
        return;
      }

      try {
        const status = await api.getBriefGenerationStatus(currentTaskId);
        
        // 检查是否有新日志
        if (status.logs.length > lastLogCountRef.current) {
          onLogUpdateRef.current?.(status.logs);
          lastLogCountRef.current = status.logs.length;
        }

        // 检查任务状态
        if (status.status === 'completed') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onCompleteRef.current?.(status.result || '');
        } else if (status.status === 'failed') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onErrorRef.current?.(status.error || '任务执行失败');
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
          onErrorRef.current?.('任务不存在或已被清理');
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
  }, [taskId, enabled, interval]); // 移除了回调函数的依赖，避免频繁重新设置轮询
};
