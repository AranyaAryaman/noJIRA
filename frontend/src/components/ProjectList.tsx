import { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { Project } from '../types';

interface Props {
  onSelectProject: (project: Project) => void;
  selectedProjectId?: number;
}

export function ProjectList({ onSelectProject, selectedProjectId }: Props) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await api.listProjects();
      setProjects(data);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    const project = await api.createProject({
      name: newName,
      description: newDesc || undefined,
    });
    setProjects([...projects, project]);
    setNewName('');
    setNewDesc('');
    setShowCreate(false);
    onSelectProject(project);
  };

  if (loading) {
    return <div className="sidebar">Loading...</div>;
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Projects</h2>
        <button className="btn-icon" onClick={() => setShowCreate(!showCreate)}>
          +
        </button>
      </div>

      {showCreate && (
        <form className="create-form" onSubmit={handleCreate}>
          <input
            type="text"
            placeholder="Project name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            autoFocus
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
          />
          <div className="form-actions">
            <button type="submit">Create</button>
            <button type="button" onClick={() => setShowCreate(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <ul className="project-list">
        {projects.map((project) => (
          <li
            key={project.project_id}
            className={selectedProjectId === project.project_id ? 'active' : ''}
            onClick={() => onSelectProject(project)}
          >
            <span className="project-name">{project.name}</span>
            {project.is_archived && <span className="badge">Archived</span>}
          </li>
        ))}
      </ul>

      {projects.length === 0 && !showCreate && (
        <p className="empty-state">No projects yet. Create one to get started!</p>
      )}
    </div>
  );
}
