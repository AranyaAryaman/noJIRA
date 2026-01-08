const API_BASE = '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('token');

  const headers: HeadersInit = {
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  // Auth
  register: (data: { name: string; email: string; password: string; nickname?: string }) =>
    request<{ person_id: number }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  login: (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
  },

  getMe: () => request<import('./client').Person>('/auth/me'),

  // Projects
  listProjects: (includeArchived = false) =>
    request<import('./client').Project[]>(`/projects?include_archived=${includeArchived}`),

  getProject: (id: number) =>
    request<import('./client').ProjectWithDetails>(`/projects/${id}`),

  createProject: (data: { name: string; description?: string }) =>
    request<import('./client').Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateProject: (id: number, data: { name?: string; description?: string; is_archived?: boolean }) =>
    request<import('./client').Project>(`/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  addProjectMember: (projectId: number, personId: number, role: string) =>
    request(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify({ person_id: personId, role }),
    }),

  // Teams
  listTeams: () => request<import('./client').Team[]>('/teams'),

  getTeam: (id: number) =>
    request<import('./client').TeamWithMembers>(`/teams/${id}`),

  createTeam: (data: { name: string; description?: string }) =>
    request<import('./client').Team>('/teams', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Tasks
  listTasks: (projectId: number, filters?: { status?: string; assignee_id?: number; severity?: number }) => {
    const params = new URLSearchParams({ project_id: String(projectId) });
    if (filters?.status) params.append('status', filters.status);
    if (filters?.assignee_id) params.append('assignee_id', String(filters.assignee_id));
    if (filters?.severity) params.append('severity', String(filters.severity));
    return request<import('./client').Task[]>(`/tasks?${params}`);
  },

  getTask: (id: number) => request<import('./client').Task>(`/tasks/${id}`),

  createTask: (data: {
    project_id: number;
    name: string;
    description?: string;
    assignee_id?: number;
    status?: string;
    severity?: number;
    priority?: number;
    due_date?: string;
    tags?: string[];
  }) =>
    request<import('./client').Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateTask: (id: number, data: {
    name?: string;
    description?: string;
    assignee_id?: number | null;
    status?: string;
    severity?: number;
    priority?: number;
    due_date?: string;
    is_archived?: boolean;
    tags?: string[];
  }) =>
    request<import('./client').Task>(`/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteTask: (id: number) =>
    request(`/tasks/${id}`, { method: 'DELETE' }),

  // Comments
  listComments: (taskId: number) =>
    request<import('./client').Comment[]>(`/comments/task/${taskId}`),

  createComment: (taskId: number, text: string) =>
    request<import('./client').Comment>('/comments', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, text }),
    }),

  updateComment: (id: number, text: string) =>
    request<import('./client').Comment>(`/comments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ text }),
    }),

  deleteComment: (id: number) =>
    request(`/comments/${id}`, { method: 'DELETE' }),

  // Attachments
  uploadTaskAttachment: (taskId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<{ attachment_id: number }>(`/attachments/task/${taskId}`, {
      method: 'POST',
      body: formData,
    });
  },

  downloadTaskAttachment: (attachmentId: number) =>
    `${API_BASE}/attachments/task/${attachmentId}/download`,

  deleteTaskAttachment: (attachmentId: number) =>
    request(`/attachments/task/${attachmentId}`, { method: 'DELETE' }),
};

// Re-export types for convenience
export type { Person, Project, ProjectWithDetails, Team, TeamWithMembers, Task, Comment } from '../types';
