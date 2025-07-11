import { create } from 'zustand';
import { OptionsObject, SnackbarKey, SnackbarMessage } from 'notistack';

interface NotificationState {
  enqueueSnackbar: (message: SnackbarMessage, options?: OptionsObject) => SnackbarKey | null;
  closeSnackbar: (key?: SnackbarKey) => void;
  setEnqueueSnackbar: (enqueue: any) => void; // Function to be set by Notistack provider
  setCloseSnackbar: (close: any) => void;   // Function to be set by Notistack provider
}

export const useNotificationStore = create<NotificationState>((set) => ({
  enqueueSnackbar: () => {
    console.warn('enqueueSnackbar called before Notistack provider is ready.');
    return null;
  },
  closeSnackbar: () => {
    console.warn('closeSnackbar called before Notistack provider is ready.');
  },
  setEnqueueSnackbar: (enqueue) => set({ enqueueSnackbar: enqueue }),
  setCloseSnackbar: (close) => set({ closeSnackbar: close }),
}));

// Helper functions (can be part of the store or separate)
export const showSuccess = (message: string) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'success' });
};

export const showError = (message: string) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'error' });
};

export const showInfo = (message: string) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'info' });
};

export const showWarning = (message: string) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'warning' });
};
