// frontend/src/modules/recurso_judicial/recursoJudicialStore.ts
import { create } from 'zustand';
import { RespostaQuesitos } from '../../services/api'; // Adjusted path
import simulatedResponseText from './docs/recurso_judicial.txt?raw'; // Changed import path

interface RecursoJudicialState { // Changed interface name
  isLoading: boolean;
  error: string | null;
  recursoJudicialResult: string | null; // Changed result variable name
  currentFileBeingProcessed: File | null;
}

interface RecursoJudicialActions { // Changed interface name
  gerarRecursoJudicial: (file: File) => void; // Changed function name
  clearState: () => void;
}

const initialState: RecursoJudicialState = { // Changed interface name
  isLoading: false,
  error: null,
  recursoJudicialResult: null, // Changed result variable name
  currentFileBeingProcessed: null,
};

export const useRecursoJudicialStore = create<RecursoJudicialState & RecursoJudicialActions>((set) => ({ // Changed store hook and interface names
  ...initialState,

  gerarRecursoJudicial: (file: File) => { // Changed function name
    set({
      isLoading: true,
      error: null,
      recursoJudicialResult: null, // Changed result variable name
      currentFileBeingProcessed: file,
    });

    const randomDelay = Math.floor(Math.random() * (12000 - 5000 + 1)) + 5000;
    setTimeout(() => {
      const simulatedResult: RespostaQuesitos = {
        quesitos_texto: simulatedResponseText,
      };
      set({
        recursoJudicialResult: simulatedResult.quesitos_texto, // Changed result variable name
        isLoading: false,
        currentFileBeingProcessed: null,
      });
    }, randomDelay);
  },

  clearState: () => {
    set(initialState);
  },
}));
