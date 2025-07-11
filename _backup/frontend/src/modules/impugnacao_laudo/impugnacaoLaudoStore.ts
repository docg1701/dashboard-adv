// frontend/src/stores/impugnacaoLaudoStore.ts
import { create } from 'zustand';
import { RespostaQuesitos } from '../services/api'; // Re-using this type for simplicity
import simulatedResponseText from './docs/impugnacao_laudo.txt?raw';

interface ImpugnacaoLaudoState {
  isLoading: boolean;
  error: string | null;
  impugnacaoResult: string | null;
  currentFileBeingProcessed: File | null;
}

interface ImpugnacaoLaudoActions {
  gerarImpugnacao: (file: File) => void;
  clearState: () => void;
}

const initialState: ImpugnacaoLaudoState = {
  isLoading: false,
  error: null,
  impugnacaoResult: null,
  currentFileBeingProcessed: null,
};

export const useImpugnacaoLaudoStore = create<ImpugnacaoLaudoState & ImpugnacaoLaudoActions>((set) => ({
  ...initialState,

  gerarImpugnacao: (file: File) => {
    set({
      isLoading: true,
      error: null,
      impugnacaoResult: null,
      currentFileBeingProcessed: file,
    });

    const randomDelay = Math.floor(Math.random() * (12000 - 5000 + 1)) + 5000;
    setTimeout(() => {
      const simulatedResult: RespostaQuesitos = {
        quesitos_texto: simulatedResponseText,
      };
      set({
        impugnacaoResult: simulatedResult.quesitos_texto,
        isLoading: false,
        currentFileBeingProcessed: null,
      });
    }, randomDelay);
  },

  clearState: () => {
    set(initialState);
  },
}));
