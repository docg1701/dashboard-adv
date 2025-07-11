// frontend/src/services/api.ts

// Read the API base URL from environment variables populated by Vite
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// --- Type Definitions ---

// System Info Module
export interface SystemInfoResponse {
    environment: string;
    project_name: string;
    server_time_utc: string;
    api_prefix: string;
}

// Gerador Quesitos Module
export interface RespostaQuesitos {
    quesitos_texto: string;
}

// Auth Module
export interface LoginResponse {
    access_token: string;
    token_type: string;
}

export interface UserBase {
  email: string;
}

export interface UserResponse {
    id: number;
    email: string;
    role: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface UserCreate {
    email: string;
    password: string;
    role: string;
    is_active?: boolean;
}

export interface UserUpdateRequest {
    email?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
}

export interface UserListResponse {
  items: UserResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}


// --- Generic API Client (for JSON endpoints) ---
async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = localStorage.getItem('token');

    const defaultHeaders: HeadersInit = {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
    };

    const config: RequestInit = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            let errorData;
            try { errorData = await response.json(); } catch (e) { /* Ignore */ }
            throw new Error(`API request failed: ${response.status} ${response.statusText}${errorData ? ` - ${JSON.stringify(errorData)}` : ''}`);
        }
        if (response.status === 204) { return {} as T; }
        return await response.json() as T;
    } catch (error) {
        console.error('API Client Error:', error);
        throw error;
    }
}

// --- Specific API Functions ---

/** Fetches system status information from the backend. */
export const getSystemInfo = (): Promise<SystemInfoResponse> => {
    return apiClient<SystemInfoResponse>('/info/v1/status');
};

/**
 * Uploads a PDF and form data to generate quesitos directly.
 * This is a synchronous, multipart/form-data request.
 */
export const gerarQuesitosDiretamente = async (
    file: File,
    beneficio: string,
    profissao: string,
    modelo_nome: string
): Promise<RespostaQuesitos> => {
    const url = `${API_BASE_URL}/gerador_quesitos/v1/gerar`;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('beneficio', beneficio);
    formData.append('profissao', profissao);
    formData.append('modelo_nome', modelo_nome);

    const token = localStorage.getItem('token');
    const headers: HeadersInit = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    // Do NOT set 'Content-Type' for FormData, the browser handles it correctly with the boundary.

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData,
        });
        if (!response.ok) {
            let errorData;
            try { errorData = await response.json(); } catch (e) { /* Ignore */ }
            throw new Error(`API request failed: ${response.status} ${response.statusText}${errorData ? ` - ${JSON.stringify(errorData)}` : ''}`);
        }
        return await response.json() as RespostaQuesitos;
    } catch (error) {
        console.error('Error in gerarQuesitosDiretamente:', error);
        throw error;
    }
};


/** Logs in a user and returns a JWT token. */
export const login = async (email: string, password: string): Promise<LoginResponse> => {
    const url = `${API_BASE_URL}/auth/v1/login`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                username: email,
                password,
                grant_type: 'password',
                client_id: 'string',
                client_secret: 'string',
            }),
        });
        if (!response.ok) {
            let errorData;
            try { errorData = await response.json(); } catch (e) { /* Ignore */ }
            throw new Error(`Login failed: ${response.status} ${response.statusText}${errorData ? ` - ${JSON.stringify(errorData)}` : ''}`);
        }
        const data = await response.json() as LoginResponse;
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
        }
        return data;
    } catch (error) {
        console.error('Error in login:', error);
        throw error;
    }
};

/** Fetches the current user's information. */
export const getCurrentUser = async (token: string): Promise<UserResponse> => {
    return apiClient<UserResponse>('/auth/v1/users/me', {
        headers: { Authorization: `Bearer ${token}` },
    });
};

/** Fetches all users (admin only) with pagination. */
export const getUsers = async (skip: number, limit: number): Promise<UserListResponse> => {
    return apiClient<UserListResponse>(`/auth/v1/admin/users?skip=${skip}&limit=${limit}`);
};

/** Fetches a specific user by ID (admin only). */
export const getUser = async (userId: number): Promise<UserResponse> => {
    return apiClient<UserResponse>(`/auth/v1/admin/users/${userId}`);
};

/** Creates a new user (admin only). */
export const createUser = async (user: UserCreate): Promise<UserResponse> => {
    return apiClient<UserResponse>('/auth/v1/admin/users', {
        method: 'POST',
        body: JSON.stringify(user),
    });
};

/** Updates a user (admin only). */
export const updateUser = async (userId: number, user: UserUpdateRequest): Promise<UserResponse> => {
    return apiClient<UserResponse>(`/auth/v1/admin/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify(user),
    });
};

/** Deletes a user (admin only). */
export const deleteUser = async (userId: number): Promise<void> => {
    return apiClient<void>(`/auth/v1/admin/users/${userId}`, {
        method: 'DELETE',
    });
};
