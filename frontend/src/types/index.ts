export type TaskStatus = 'NOT_STARTED' | 'PLANNING' | 'DEVELOPMENT' | 'TESTING' | 'FINISHED';
export type ProjectRole = 'ADMIN' | 'MEMBER' | 'VIEWER';
export type TeamRole = 'OWNER' | 'MEMBER';

export interface Person {
  person_id: number;
  name: string;
  email: string;
  nickname?: string;
  created_at: string;
}

export interface PersonBrief {
  person_id: number;
  name: string;
  email: string;
  nickname?: string;
}

export interface Team {
  team_id: number;
  name: string;
  description?: string;
  created_by: number;
  created_at: string;
}

export interface TeamMember {
  person: PersonBrief;
  role: TeamRole;
}

export interface TeamWithMembers extends Team {
  members: TeamMember[];
}

export interface Project {
  project_id: number;
  name: string;
  description?: string;
  created_by: number;
  created_at: string;
  is_archived: boolean;
}

export interface ProjectMember {
  person: PersonBrief;
  role: ProjectRole;
}

export interface ProjectTeam {
  team: Team;
}

export interface ProjectWithDetails extends Project {
  members: ProjectMember[];
  teams: ProjectTeam[];
}

export interface TaskTag {
  tag: string;
}

export interface TaskAttachment {
  attachment_id: number;
  file_name: string;
  file_type: string;
  uploaded_by: number;
  uploaded_at: string;
}

export interface Task {
  task_id: number;
  project_id: number;
  parent_task_id?: number;
  name: string;
  description?: string;
  assignee_id?: number;
  status: TaskStatus;
  severity: number;
  priority: number;
  due_date?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  tags: TaskTag[];
  assignee?: PersonBrief;
  creator?: PersonBrief;
  attachments: TaskAttachment[];
  subtask_count: number;
}

export interface CommentAttachment {
  attachment_id: number;
  file_name: string;
  file_type: string;
  uploaded_at: string;
}

export interface Comment {
  comment_id: number;
  task_id: number;
  person_id: number;
  text: string;
  is_system_comment: boolean;
  created_at: string;
  edited_at?: string;
  person?: PersonBrief;
  attachments: CommentAttachment[];
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}
