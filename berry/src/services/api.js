// berry/src/services/api.js

// Read the API base URL from environment variables populated by Vite
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// --- Generic API Client (for JSON endpoints) ---
async function apiClient(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = localStorage.getItem('token');

    const defaultHeaders = {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
    };

    const config = {
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
        if (response.status === 204) { return {}; }
        return await response.json();
    } catch (error) {
        console.error('API Client Error:', error);
        throw error;
    }
}

// --- Specific API Functions ---

/** Fetches system status information from the backend. */
export const getSystemInfo = () => {
    return apiClient('/info/v1/status');
};

/**
 * Uploads a PDF and form data to generate quesitos directly.
 * This is a synchronous, multipart/form-data request.
 */
export const gerarQuesitosDiretamente = async (
    file,
    beneficio,
    profissao,
    modelo_nome
) => {
    const url = `${API_BASE_URL}/gerador_quesitos/v1/gerar`;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('beneficio', beneficio);
    formData.append('profissao', profissao);
    formData.append('modelo_nome', modelo_nome);

    const token = localStorage.getItem('token');
    const headers = {};
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
        return await response.json();
    } catch (error) {
        console.error('Error in gerarQuesitosDiretamente:', error);
        throw error;
    }
};


/** Logs in a user and returns a JWT token. */
export const login = async (email, password) => {
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
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || 'Login failed');
        }
        const data = await response.json();
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
export const getCurrentUser = async (token) => {
    return apiClient('/auth/v1/users/me', {
        headers: { Authorization: `Bearer ${token}` },
    });
};

/** Fetches all users (admin only) with pagination. */
export const getUsers = async (skip, limit) => {
    return apiClient(`/auth/v1/admin/users?skip=${skip}&limit=${limit}`);
};

/** Fetches a specific user by ID (admin only). */
export const getUser = async (userId) => {
    return apiClient(`/auth/v1/admin/users/${userId}`);
};

/** Creates a new user (admin only). */
export const createUser = async (user) => {
    return apiClient('/auth/v1/admin/users', {
        method: 'POST',
        body: JSON.stringify(user),
    });
};

/** Updates a user (admin only). */
export const updateUser = async (userId, user) => {
    return apiClient(`/auth/v1/admin/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify(user),
    });
};

/** Deletes a user (admin only). */
export const deleteUser = async (userId) => {
    return apiClient(`/auth/v1/admin/users/${userId}`, {
        method: 'DELETE',
    });
};

/**
 * Uploads a PDF file to generate a "recurso judicial".
 * This is a synchronous, multipart/form-data request.
 */
export const gerarRecursoJudicial = async (file) => {
    const url = `${API_BASE_URL}/recurso_judicial/v1/gerar`;
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');
    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

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
        return await response.json();
    } catch (error) {
        console.error('Error in gerarRecursoJudicial:', error);
        throw error;
    }
};
