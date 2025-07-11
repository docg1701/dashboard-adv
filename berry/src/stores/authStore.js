import { create } from 'zustand';
import { login as apiLogin, getCurrentUser as apiGetCurrentUser } from '../services/api';

export const useAuthStore = create((set, get) => ({
  token: localStorage.getItem('token'),
  user: null,
  isLoading: true,
  error: null,

  initializeAuth: async () => {
    const token = get().token;
    if (token) {
      try {
        const user = await apiGetCurrentUser(token);
        set({ user, isLoading: false });
      } catch (error) {
        console.error("Failed to fetch user on init:", error);
        localStorage.removeItem('token');
        set({ token: null, user: null, isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiLogin(email, password);
      const user = await apiGetCurrentUser(data.access_token);
      set({ token: data.access_token, user, isLoading: false });
    } catch (error) {
      const errorMessage = error.message || 'Falha no login.';
      set({ error: errorMessage, isLoading: false, token: null, user: null });
      localStorage.removeItem('token');
      throw error; // Re-throw error to be caught by the component
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null, isLoading: false });
  },
}));
