// berry/src/stores/recursoJudicialStore.js
import { create } from 'zustand';
import simulatedResponseText from './docs/recurso_judicial.txt?raw';

const initialState = {
  isLoading: false,
  error: null,
  recursoJudicialResult: null,
  currentFileBeingProcessed: null
};

export const useRecursoJudicialStore = create((set) => ({
  ...initialState,

  gerarRecurso: (file) => {
    set({
      isLoading: true,
      error: null,
      recursoJudicialResult: null,
      currentFileBeingProcessed: file
    });

    // Simulate API call delay
    const randomDelay = Math.floor(Math.random() * (8000 - 3000 + 1)) + 3000;

    setTimeout(() => {
      set({
        recursoJudicialResult: simulatedResponseText,
        isLoading: false,
        currentFileBeingProcessed: null
      });
    }, randomDelay);
  },

  clearState: () => {
    set(initialState);
  }
}));