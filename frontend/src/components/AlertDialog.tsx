import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialog as AlertDialogComponent,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogPortal,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@radix-ui/react-alert-dialog";

interface AlertDialogProps {
  trigger: React.ReactNode;
  title: string;
  description: string;
  confirmText: string;
  onConfirm: () => void;
}

export const AlertDialog = ({
  trigger,
  title,
  description,
  confirmText,
  onConfirm,
}: AlertDialogProps) => {
  return (
    <AlertDialogComponent>
      <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>
      <AlertDialogPortal>
        <AlertDialogContent className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
            <AlertDialogTitle className="text-lg font-semibold text-gray-900">
              {title}
            </AlertDialogTitle>
            <AlertDialogDescription className="mt-2 text-sm text-gray-700">
              {description}
            </AlertDialogDescription>
            <div className="flex justify-end gap-3 mt-6">
              <AlertDialogCancel className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500">
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                onClick={onConfirm}
              >
                {confirmText}
              </AlertDialogAction>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialogPortal>
    </AlertDialogComponent>
  );
};
