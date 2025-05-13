import { toast, ToastOptions } from 'react-toastify';

interface ToastConfig extends ToastOptions {
  message: string;
}

export const useToast = () => {
  const showToast = ({
    message,
    type = 'info',
    position = 'top-center',
    autoClose = 2000,
    ...rest
  }: ToastConfig) => {
    toast(message, {
      type,
      position,
      autoClose,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
      ...rest,
    });
  };

  const success = (message: string, options?: Omit<ToastConfig, 'message'>) => {
    showToast({ message, type: 'success', ...options });
  };

  const error = (message: string, options?: Omit<ToastConfig, 'message'>) => {
    showToast({ message, type: 'error', ...options });
  };

  const info = (message: string, options?: Omit<ToastConfig, 'message'>) => {
    showToast({ message, type: 'info', ...options });
  };

  const warning = (message: string, options?: Omit<ToastConfig, 'message'>) => {
    showToast({ message, type: 'warning', ...options });
  };
  const promise = <T>(
    promise: Promise<T>,
    {
      pending = 'Loading...',
      success = 'Completed successfully',
      error = 'Something went wrong',
      ...options
    }: {
      pending?: string;
      success?: string;
      error?: string;
      options?: Omit<ToastConfig, 'message'>;
    } = {}
  ) => {
    return toast.promise(promise, {
      pending,
      success,
      error,
      ...options
    });
  };

  return {
    showToast,
    success,
    error,
    info,
    warning,
    promise,
  };
};
