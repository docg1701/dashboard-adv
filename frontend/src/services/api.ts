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

export interface GerarQuesitosPayload { // New payload for refactored endpoint
  document_filename: string; // Changed from document_id: number
  beneficio: string;
  profissao: string;
  modelo_nome: string;
}

// Auth Module
export interface LoginResponse {
    access_token: string;
    token_type: string;
}

// New UserBase interface
export interface UserBase {
  email: string;
}

export interface UserResponse { // Kept as is
    id: number;
    email: string;
    role: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface UserCreate { // Renamed from UserCreateRequest and modified
    email: string;
    password: string;
    role: string;
    is_active?: boolean; // Make optional, backend defaults if not sent
}

export interface UserUpdateRequest { // Kept as is
    email?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
}

// New UserListResponse interface
export interface UserListResponse {
  items: UserResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Document Analysis Module
export interface DocumentUploadResponse {
  message: string; // Gateway message
  transcriber_data: {
    task_id: string;
    message: string; // Transcritor service message
  };
  original_filename: string;
  uploader_user_id: number; // Or string, depending on User model
}

export interface TaskStatusErrorInfo {
  error?: string | null;
  traceback?: string | null;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string; // e.g., "PENDING", "STARTED", "SUCCESS", "FAILURE", "RETRY" (Celery statuses)
  result?: any | null;
  error_info?: TaskStatusErrorInfo | null;
}

// Document Query
export interface DocumentQueryPayload {
  user_query: string; // Changed from query_text to match backend Pydantic model
}

export interface DocumentQueryResponse {
  answer: string;
  query_id: string; // Assuming the backend returns a query_id
}

// ProcessedDocumentInfo is removed as its associated endpoint /documents/upload-and-process is deprecated.
// export interface ProcessedDocumentInfo {
//   id: number;
//   file_hash: string;
//   file_name: string | null;
//   created_at: string;
//   updated_at: string | null;
// }


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

// /** Uploads PDF and inputs to generate quesitos. Uses FormData. (OLD - to be removed or refactored) */
// export const postGerarQuesitos = async (formData: FormData): Promise<RespostaQuesitos> => {
//     const url = `${API_BASE_URL}/gerador_quesitos/v1/gerar`;
//     try {
//         const response = await fetch(url, {
//             method: 'POST',
//             body: formData,
//         });
//         if (!response.ok) {
//             let errorData;
//             try { errorData = await response.json(); } catch (e) { /* Ignore */ }
//             throw new Error(`API request failed: ${response.status} ${response.statusText}${errorData ? ` - ${JSON.stringify(errorData)}` : ''}`);
//         }
//         return await response.json() as RespostaQuesitos;
//     } catch (error) {
//         console.error('Error in postGerarQuesitos:', error);
//         throw error;
//     }
// };

// Placeholder - will be implemented in TASK-058 for backend changes
export const postGerarQuesitosComReferenciaDeDocumento = async (payload: GerarQuesitosPayload): Promise<RespostaQuesitos> => {
  console.log('Placeholder: postGerarQuesitosComReferenciaDeDocumento called with', payload);
  // This will eventually call the refactored backend for gerador_quesitos
  // For now, return a dummy response or throw an error indicating it's not implemented
  // Example: return { quesitos_texto: "Quesitos (refatorados) para doc ID: " + payload.document_id };
  return apiClient<RespostaQuesitos>('/gerador_quesitos/v1/gerar_com_referencia_documento', { // New endpoint path
      method: 'POST',
      body: JSON.stringify(payload),
  });
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
            // No global axios instance to update, apiClient reads from localStorage each time
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
export const createUser = async (user: UserCreate): Promise<UserResponse> => { // Parameter type updated
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

/** Uploads a document for analysis. */
export const uploadDocumentForAnalysis = async (file: File): Promise<DocumentUploadResponse> => {
  const url = `${API_BASE_URL}/documents/upload`; // Reverted: Path relative to API_BASE_URL
  const formData = new FormData();
  formData.append('file', file); // 'file' is the key used in backend by `UploadFile = File(...)`

  const token = localStorage.getItem('token');
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  // Do NOT set Content-Type for FormData, browser does it with boundary.

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
    return await response.json() as DocumentUploadResponse;
  } catch (error) {
    console.error('Error in uploadDocumentForAnalysis:', error);
    throw error; // Re-throw to be caught by the calling component
  }
};

/** Fetches the status of a document processing task. */
export const getTaskStatus = (taskId: string): Promise<TaskStatusResponse> => {
  return apiClient<TaskStatusResponse>(`/documents/upload/status/${taskId}`);
};

/** Posts a query against a processed document. */
export const postDocumentQuery = async (
  documentId: string,
  payload: DocumentQueryPayload
): Promise<DocumentQueryResponse> => {
  return apiClient<DocumentQueryResponse>(`/documents/query/${documentId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

// The deprecated function uploadAndProcessPdf and its associated comments have been removed.
// The main document upload functionality is handled by uploadDocumentForAnalysis.

// The following block was a duplicated, non-functional leftover and has been removed.
// formData.append('file', file);
// const token = localStorage.getItem('token');
// const headers: HeadersInit = {};
// if (token) {
//   headers['Authorization'] = `Bearer ${token}`;
// }
// try {
//   const response = await fetch(url, {
//     method: 'POST',
//     headers,
//     body: formData,
//   });
//   if (!response.ok) {
//     let errorData;
//     try { errorData = await response.json(); } catch (e) { /* Ignore */ }
//     const detail = errorData?.detail || `API request failed: ${response.status} ${response.statusText}`;
//     throw new Error(String(detail));
//   }
//   return await response.json() as ProcessedDocumentInfo;
// } catch (error) {
//   console.error('Error in uploadAndProcessPdf:', error);
//   throw error;
// }
// };