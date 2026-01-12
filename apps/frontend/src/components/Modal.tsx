import type { PropsWithChildren } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  onConfirm?: () => void;
  confirmText?: string;
}

export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  onConfirm,
  confirmText = '保存',
}: PropsWithChildren<ModalProps>) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="bg-white w-full max-w-lg rounded-[2.5rem] shadow-2xl relative z-10 overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="px-8 pt-8 pb-4 flex justify-between items-center border-b border-slate-50">
          <h3 className="text-xl font-black text-slate-800 tracking-tight">
            {title}
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-50 rounded-full text-slate-400 transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <div className="px-8 py-6 text-slate-600 max-h-[60vh] overflow-y-auto custom-scrollbar">
          {children}
        </div>
        <div className="px-8 pb-8 pt-4 flex gap-3 border-t border-slate-50">
          <button
            onClick={onClose}
            className="flex-1 py-3 rounded-2xl font-bold text-slate-400 hover:bg-slate-50 transition-all"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-3 rounded-2xl font-bold bg-indigo-600 text-white shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};
