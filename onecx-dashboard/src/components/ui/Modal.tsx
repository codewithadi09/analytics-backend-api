import type { ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-900/20 px-4">
      <div className="w-full max-w-sm rounded-lg border border-zinc-200 bg-white p-5 shadow-lg">
        <h2 className="mb-4 text-base font-medium text-zinc-900">{title}</h2>
        {children}
      </div>
      {/* Click-outside-to-close target, kept behind the modal box */}
      <button
        aria-label="Close"
        onClick={onClose}
        className="fixed inset-0 -z-10 cursor-default"
        tabIndex={-1}
      />
    </div>
  );
}

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isDestructive?: boolean;
  isLoading?: boolean;
}

export function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  onConfirm,
  onCancel,
  isDestructive = true,
  isLoading = false,
}: ConfirmModalProps) {
  return (
    <Modal open={open} onClose={onCancel} title={title}>
      <p className="mb-5 text-sm text-zinc-600">{message}</p>
      <div className="flex justify-end gap-3">
        <button className="btn-text" onClick={onCancel} disabled={isLoading}>
          Cancel
        </button>
        <button
          className={isDestructive ? "btn-destructive" : "btn-primary"}
          onClick={onConfirm}
          disabled={isLoading}
        >
          {isLoading ? "Working…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
