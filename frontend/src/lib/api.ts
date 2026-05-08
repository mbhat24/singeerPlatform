const API_BASE = "/api";

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const config: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}${endpoint}`, config);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(error.detail || "Request failed", res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface User {
  id: string;
  email: string;
  display_name: string;
}

export interface VoiceProfile {
  id: string;
  name: string;
  duration_seconds: number;
  status: "pending" | "processing" | "completed" | "failed";
}

export interface Project {
  id: string;
  voice_profile_id: string;
  title: string;
  lyrics: string;
  status: "pending" | "processing" | "completed" | "failed";
  error_message: string | null;
  output_audio_path: string | null;
  created_at: string;
  completed_at: string | null;
}

export const api = {
  // Auth
  signup: (data: { email: string; password: string; display_name: string }) =>
    request<{ access_token: string; user: User }>("/auth/signup", {
      method: "POST",
      body: data,
    }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: data,
    }),

  getMe: () => request<User>("/auth/me"),

  // Voice profiles
  listVoices: () => request<{ profiles: VoiceProfile[] }>("/voices/"),

  getVoice: (id: string) => request<VoiceProfile>(`/voices/${id}`),

  uploadVoice: async (name: string, file: File) => {
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(
      `${API_BASE}/voices/upload?name=${encodeURIComponent(name)}`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new ApiError(err.detail, res.status);
    }
    return res.json() as Promise<VoiceProfile>;
  },

  deleteVoice: (id: string) =>
    request<void>(`/voices/${id}`, { method: "DELETE" }),

  // Projects
  listProjects: () => request<{ projects: Project[] }>("/projects/"),

  createProject: (data: {
    voice_profile_id: string;
    title: string;
    lyrics: string;
  }) =>
    request<Project>("/projects/", { method: "POST", body: data }),

  getProject: (id: string) => request<Project>(`/projects/${id}`),

  uploadReferenceAudio: async (projectId: string, file: File) => {
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(
      `${API_BASE}/projects/${projectId}/reference-audio`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new ApiError(err.detail, res.status);
    }
    return res.json();
  },

  deleteProject: (id: string) =>
    request<void>(`/projects/${id}`, { method: "DELETE" }),

  getDownloadUrl: (projectId: string) =>
    `${API_BASE}/projects/${projectId}/download`,
};

export { ApiError };
