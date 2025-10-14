import type { FC } from 'react';

export type ToastType = 'success' | 'error';

export type ToastItem = {
  id: number;
  message: string;
  type: ToastType;
};

type ToastContainerProps = {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
};

const iconForType: Record<ToastType, string> = {
  success: '+',
  error: '!',
};

export const ToastContainer: FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast--${toast.type}`} role="status">
          <span className="toast-icon" aria-hidden="true">{iconForType[toast.type]}</span>
          <span className="toast-message">{toast.message}</span>
          <button
            type="button"
            className="toast-close"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss notification"
          >
            x
          </button>
        </div>
      ))}
    </div>
  );
};
