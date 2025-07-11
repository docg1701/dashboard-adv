// frontend/src/stores/geradorQuesitosStore.ts
import { create } from 'zustand';
import { RespostaQuesitos } from '../services/api';
import simulatedResponseText from './docs/gerador_quesitos.txt?raw';

interface GeradorQuesitosState {
  isLoading: boolean;
  error: string | null;
  quesitosResult: string | null;
  currentFileBeingProcessed: File | null;
}

interface GeradorQuesitosActions {
  gerarQuesitos: (file: File, beneficio: string, profissao: string) => void;
  clearState: () => void;
}

const initialState: GeradorQuesitosState = {
  isLoading: false,
  error: null,
  quesitosResult: null,
  currentFileBeingProcessed: null,
};

// --- IMPLEMENTAÇÃO COM SIMULAÇÃO ATIVA ---
export const useGeradorQuesitosStore = create<GeradorQuesitosState & GeradorQuesitosActions>((set) => ({
  ...initialState,

  gerarQuesitos: (file: File, beneficio: string, profissao: string) => {
    set({
      isLoading: true,
      error: null,
      quesitosResult: null,
      currentFileBeingProcessed: file,
    });

    // Simulação de chamada de API com delay
    const randomDelay = Math.floor(Math.random() * (12000 - 5000 + 1)) + 5000; // Random delay between 5 and 12 seconds
    setTimeout(() => {
      // Simular sucesso usando o conteúdo do arquivo de texto importado
      const simulatedResult: RespostaQuesitos = {
        quesitos_texto: simulatedResponseText,
      };
      set({
        quesitosResult: simulatedResult.quesitos_texto,
        isLoading: false,
        currentFileBeingProcessed: null,
      });

      // Para simular um erro, comente o bloco de sucesso acima e descomente o de baixo
      // set({
      //   error: "Erro simulado: A API de simulação falhou em sua missão.",
      //   isLoading: false,
      //   currentFileBeingProcessed: null,
      // });

    }, randomDelay); // Use the random delay
  },

  clearState: () => {
    set(initialState);
  },
}));
