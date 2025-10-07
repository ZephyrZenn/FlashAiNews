import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type PropsWithChildren,
} from 'react';

import { ConfirmDialog, type ConfirmDialogOptions } from '@/components/ConfirmDialog';

type ConfirmContextValue = {
  confirm: (options?: ConfirmDialogOptions) => Promise<boolean>;
};

const ConfirmDialogContext = createContext<ConfirmContextValue | undefined>(undefined);

export const ConfirmDialogProvider = ({ children }: PropsWithChildren): JSX.Element => {
  const [options, setOptions] = useState<ConfirmDialogOptions | null>(null);
  const resolverRef = useRef<((value: boolean) => void) | null>(null);

  const closeDialog = useCallback((result: boolean) => {
    resolverRef.current?.(result);
    resolverRef.current = null;
    setOptions(null);
  }, []);

  const confirm = useCallback((dialogOptions: ConfirmDialogOptions = {}) => {
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
      setOptions(dialogOptions);
    });
  }, []);

  const handleCancel = useCallback(() => {
    closeDialog(false);
  }, [closeDialog]);

  const handleConfirm = useCallback(() => {
    closeDialog(true);
  }, [closeDialog]);

  return (
    <ConfirmDialogContext.Provider value={{ confirm }}>
      {children}
      <ConfirmDialog
        open={Boolean(options)}
        options={options}
        onCancel={handleCancel}
        onConfirm={handleConfirm}
      />
    </ConfirmDialogContext.Provider>
  );
};

export const useConfirm = (): ConfirmContextValue => {
  const context = useContext(ConfirmDialogContext);
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmDialogProvider');
  }
  return context;
};
