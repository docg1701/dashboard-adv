import { create } from 'zustand';
import { login as apiLogin, getCurrentUser as apiGetCurrentUser } from '../services/api'; // Renamed imports for clarity

interface User {
  id: number;
  email: string;
  role: string;
  // Add other user fields if necessary, e.g., is_active
}

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean; // New state
  initializeAuth: () => Promise<void>; // New action
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('token'), // Initial token from localStorage
  user: null,
  isLoading: true, // Start in loading state

  initializeAuth: async () => {
    const token = get().token; // Get token from current state
    if (token) {
      try {
        // The token should already be in api.ts's default headers via localStorage on load,
        // or apiClient will pick it up. For critical calls like this, passing it explicitly is safer.
        const user = await apiGetCurrentUser(token);
        set({ user, isLoading: false });
      } catch (error) {
        console.error("Failed to fetch user on init:", error);
        // Token might be invalid or expired
        localStorage.removeItem('token');
        // No global axios instance's default header to clear here, api.ts's apiClient handles it per call
        set({ token: null, user: null, isLoading: false });
      }
    } else {
      set({ isLoading: false }); // No token, not loading
    }
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true }); // Set loading true at the start of login
    try {
      // apiLogin now handles setting token in localStorage
      const { access_token } = await apiLogin(email, password);
      // Fetch user with the new token. api.ts's apiClient will use the new token from localStorage.
      const user = await apiGetCurrentUser(access_token); // Pass explicitly for this critical step
      set({ token: access_token, user, isLoading: false });
    } catch (error) {
      // Ensure localStorage is cleared if login itself failed badly after token was set by apiLogin but user fetch failed
      // However, apiLogin only sets token on *successful* response.
      // If apiLogin fails, it throws, and token isn't set in localStorage by it.
      set({ isLoading: false, token: null, user: null }); // Clear sensitive data on error
      localStorage.removeItem('token'); // Ensure token is cleared if any part of login sequence fails
      throw error; // Re-throw to allow UI to catch it
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    // No global axios instance's default header to clear here, api.ts's apiClient handles it per call
    set({ token: null, user: null, isLoading: false });
  },
}));

// Consider calling initializeAuth when the app loads, e.g., in App.tsx's useEffect.
