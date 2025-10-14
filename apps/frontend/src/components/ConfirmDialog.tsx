import type { FC } from 'react';

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
    title = 'Are you sure?',
    description = 'Please confirm to continue.',
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    tone = 'default',
  } = options;

  const confirmButtonClass = tone === 'danger' ? 'button danger' : 'button';

  return (
    <div
      className="modal-overlay"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      onClick={onCancel}
    >
      <div
        className="modal-content card confirm-dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <h3 id="confirm-dialog-title" className="section-title" style={{ marginBottom: 0 }}>
            {title}
          </h3>
          <button
            type="button"
            className="modal-close"
            aria-label="Close"
            onClick={onCancel}
          >
            ×
          </button>
        </div>
        <p id="confirm-dialog-description" className="confirm-description">
          {description}
        </p>
        <div className="modal-actions">
          <button type="button" className="button secondary" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button type="button" className={confirmButtonClass} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
