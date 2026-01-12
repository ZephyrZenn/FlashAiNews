import type { FC } from 'react';
import { X } from 'lucide-react';

export type ConfirmDialogOptions = {
  title?: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: 'default' | 'danger';
};

type ConfirmDialogProps = {
  open: boolean;
  options?: ConfirmDialogOptions | null;
  onConfirm: () => void;
  onCancel: () => void;
};

export const ConfirmDialog: FC<ConfirmDialogProps> = ({
  open,
  options,
  onConfirm,
  onCancel,
}) => {
  if (!open || !options) {
    return null;
  }

  const {
    title = '确认操作',
    description = '请确认是否继续此操作。',
    confirmLabel = '确认',
    cancelLabel = '取消',
    tone = 'default',
  } = options;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onCancel}
      />
      <div className="bg-white w-full max-w-md rounded-[2.5rem] shadow-2xl relative z-10 overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="px-8 pt-8 pb-4 flex justify-between items-center border-b border-slate-50">
          <h3 className="text-xl font-black text-slate-800 tracking-tight">
            {title}
          </h3>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-slate-50 rounded-full text-slate-400 transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <div className="px-8 py-6 text-slate-600">
          <p className="text-sm leading-relaxed">{description}</p>
        </div>
        <div className="px-8 pb-8 pt-4 flex gap-3 border-t border-slate-50">
          <button
            onClick={onCancel}
            className="flex-1 py-3 rounded-2xl font-bold text-slate-400 hover:bg-slate-50 transition-all"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 py-3 rounded-2xl font-bold shadow-lg transition-all ${
              tone === 'danger'
                ? 'bg-rose-500 text-white shadow-rose-100 hover:bg-rose-600'
                : 'bg-indigo-600 text-white shadow-indigo-100 hover:bg-indigo-700'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
