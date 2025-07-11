// berry/src/stores/analiseDocsMedicosStore.js
import { create } from 'zustand';
import simulatedResponseText from './docs/analise_docs_medicos.txt?raw';

const initialState = {
  isLoading: false,
  error: null,
  analiseResult: null,
  currentFileBeingProcessed: null
};

export const useAnaliseDocsMedicosStore = create((set) => ({
  ...initialState,

  gerarAnalise: (file) => {
    set({
      isLoading: true,
      error: null,
      analiseResult: null,
      currentFileBeingProcessed: file
    });

    // Simulate API call delay
    const randomDelay = Math.floor(Math.random() * (8000 - 3000 + 1)) + 3000;

    setTimeout(() => {
      set({
        analiseResult: simulatedResponseText,
        isLoading: false,
        currentFileBeingProcessed: null
      });
    }, randomDelay);
  },

  clearState: () => {
    set(initialState);
  }
}));
