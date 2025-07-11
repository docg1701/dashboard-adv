import { create } from 'zustand';
import simulatedResponseText from './docs/gerador_quesitos.txt?raw';

const initialState = {
  isLoading: false,
  error: null,
  quesitosResult: null,
  currentFileBeingProcessed: null,
};

export const useGeradorQuesitosStore = create((set) => ({
  ...initialState,

  gerarQuesitos: (file, beneficio, profissao) => {
    set({
      isLoading: true,
      error: null,
      quesitosResult: null,
      currentFileBeingProcessed: file,
    });

    const randomDelay = Math.floor(Math.random() * (12000 - 5000 + 1)) + 5000;
    setTimeout(() => {
      const simulatedResult = {
        quesitos_texto: simulatedResponseText,
      };
      set({
        quesitosResult: simulatedResult.quesitos_texto,
        isLoading: false,
        currentFileBeingProcessed: null,
      });
    }, randomDelay);
  },

  clearState: () => {
    set(initialState);
  },
}));
