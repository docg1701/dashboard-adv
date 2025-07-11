// berry/src/stores/impugnacaoLaudoStore.js
import { create } from 'zustand';
import simulatedResponseText from './docs/impugnacao_laudo.txt?raw';

const initialState = {
  isLoading: false,
  error: null,
  impugnacaoResult: null,
  currentFileBeingProcessed: null
};

export const useImpugnacaoLaudoStore = create((set) => ({
  ...initialState,

  gerarImpugnacao: (file) => {
    set({
      isLoading: true,
      error: null,
      impugnacaoResult: null,
      currentFileBeingProcessed: file
    });

    // Simulate API call delay
    const randomDelay = Math.floor(Math.random() * (8000 - 3000 + 1)) + 3000;

    setTimeout(() => {
      set({
        impugnacaoResult: simulatedResponseText,
        isLoading: false,
        currentFileBeingProcessed: null
      });
    }, randomDelay);
  },

  clearState: () => {
    set(initialState);
  }
}));