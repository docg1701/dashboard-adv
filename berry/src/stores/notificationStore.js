import { create } from 'zustand';

export const useNotificationStore = create((set) => ({
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

export const showSuccess = (message) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'success' });
};

export const showError = (message) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'error' });
};

export const showInfo = (message) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'info' });
};

export const showWarning = (message) => {
  useNotificationStore.getState().enqueueSnackbar(message, { variant: 'warning' });
};
