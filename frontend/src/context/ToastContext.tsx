import { createContext, useCallback, useContext, useState, type PropsWithChildren } from 'react';

import { ToastContainer, type ToastItem, type ToastType } from '@/components/ToastContainer';

type ToastOptions = {
  type?: ToastType;
  duration?: number;
};

type ToastContextValue = {
  showToast: (message: string, options?: ToastOptions) => void;
};

const DEFAULT_DURATION = 3200;

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider = ({ children }: PropsWithChildren): JSX.Element => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, options: ToastOptions = {}) => {
      const { type = 'success', duration = DEFAULT_DURATION } = options;
      const id = Date.now();

      setToasts((prev) => [...prev, { id, message, type }]);

      window.setTimeout(() => {
        dismissToast(id);
      }, duration);
    },
    [dismissToast],
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
