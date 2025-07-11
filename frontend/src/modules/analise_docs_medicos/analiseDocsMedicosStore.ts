// frontend/src/modules/analise_docs_medicos/analiseDocsMedicosStore.ts
import { create } from 'zustand';
import { RespostaQuesitos } from '../../services/api'; // Mantido para tipo, mas não para chamada
import simulatedResponseText from './docs/analise_docs_medicos.txt?raw';

interface AnaliseDocsMedicosState {
  isLoading: boolean;
  error: string | null;
  analiseResult: string | null;
  currentFileBeingProcessed: File | null;
}

interface AnaliseDocsMedicosActions {
  gerarAnalise: (file: File) => void;
  clearState: () => void;
}

const initialState: AnaliseDocsMedicosState = {
  isLoading: false,
  error: null,
  analiseResult: null,
  currentFileBeingProcessed: null,
};

export const useAnaliseDocsMedicosStore = create<AnaliseDocsMedicosState & AnaliseDocsMedicosActions>((set) => ({
  ...initialState,

  gerarAnalise: (file: File) => {
    set({
      isLoading: true,
      error: null,
      analiseResult: null,
      currentFileBeingProcessed: file,
    });

    // Simula um tempo de processamento
    const randomDelay = Math.floor(Math.random() * (8000 - 3000 + 1)) + 3000;
    setTimeout(() => {
      const simulatedResult: RespostaQuesitos = {
        quesitos_texto: simulatedResponseText,
      };
      set({
        analiseResult: simulatedResult.quesitos_texto,
        isLoading: false,
        currentFileBeingProcessed: null,
      });
    }, randomDelay);
  },

  clearState: () => {
    set(initialState);
  },
}));
