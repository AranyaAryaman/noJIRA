import { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { ProjectWithDetails, Person, ProjectRole } from '../types';

interface Props {
  project: ProjectWithDetails;
  onClose: () => void;
  onUpdate: () => void;
}

export function ProjectSettings({ project, onClose, onUpdate }: Props) {
  const [allPeople, setAllPeople] = useState<Person[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'members' | 'settings'>('members');

  useEffect(() => {
    loadPeople();
  }, []);

  const loadPeople = async () => {
    const people = await api.listPeople();
    setAllPeople(people);
  };

  const handleAddMember = async (personId: number, role: ProjectRole = 'MEMBER') => {
    setLoading(true);
    try {
      await api.addProjectMember(project.project_id, personId, role);
      onUpdate();
    } catch (error) {
      console.error('Failed to add member:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (personId: number, role: ProjectRole) => {
    setLoading(true);
    try {
      await api.updateProjectMember(project.project_id, personId, role);
      onUpdate();
    } catch (error) {
      console.error('Failed to update member:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (personId: number) => {
    if (!confirm('Remove this member from the project?')) return;
    setLoading(true);
    try {
      await api.removeProjectMember(project.project_id, personId);
      onUpdate();
    } catch (error) {
      console.error('Failed to remove member:', error);
    } finally {
      setLoading(false);
    }
  };

  const memberIds = new Set(project.members.map((m) => m.person.person_id));
  const filteredPeople = allPeople.filter(
    (p) =>
      !memberIds.has(p.person_id) &&
      (p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.email.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Project Settings</h2>
          <button className="btn-icon" onClick={onClose}>×</button>
        </div>

        <div className="settings-tabs">
          <button
            className={activeTab === 'members' ? 'active' : ''}
            onClick={() => setActiveTab('members')}
          >
            Members
          </button>
          <button
            className={activeTab === 'settings' ? 'active' : ''}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </div>

        <div className="settings-content">
          {activeTab === 'members' && (
            <>
              <div className="add-member-section">
                <h3>Add Members</h3>
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                {searchTerm && filteredPeople.length > 0 && (
                  <ul className="people-search-results">
                    {filteredPeople.slice(0, 5).map((person) => (
                      <li key={person.person_id}>
                        <div className="person-info">
                          <span className="person-avatar">
                            {person.name.charAt(0).toUpperCase()}
                          </span>
                          <div>
                            <div className="person-name">{person.name}</div>
                            <div className="person-email">{person.email}</div>
                          </div>
                        </div>
                        <button
                          className="btn-secondary"
                          onClick={() => handleAddMember(person.person_id)}
                          disabled={loading}
                        >
                          Add
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {searchTerm && filteredPeople.length === 0 && (
                  <p className="no-results">No users found. They need to register first.</p>
                )}
              </div>

              <div className="members-section">
                <h3>Current Members ({project.members.length})</h3>
                <ul className="members-list">
                  {project.members.map((member) => (
                    <li key={member.person.person_id}>
                      <div className="person-info">
                        <span className="person-avatar">
                          {member.person.name.charAt(0).toUpperCase()}
                        </span>
                        <div>
                          <div className="person-name">{member.person.name}</div>
                          <div className="person-email">{member.person.email}</div>
                        </div>
                      </div>
                      <div className="member-actions">
                        <select
                          value={member.role}
                          onChange={(e) =>
                            handleUpdateRole(member.person.person_id, e.target.value as ProjectRole)
                          }
                          disabled={loading}
                        >
                          <option value="ADMIN">Admin</option>
                          <option value="MEMBER">Member</option>
                          <option value="VIEWER">Viewer</option>
                        </select>
                        <button
                          className="btn-icon btn-danger-icon"
                          onClick={() => handleRemoveMember(member.person.person_id)}
                          disabled={loading}
                          title="Remove member"
                        >
                          ×
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}

          {activeTab === 'settings' && (
            <div className="project-settings-form">
              <p className="settings-info">
                Project: <strong>{project.name}</strong>
              </p>
              <p className="settings-info">
                Created: {new Date(project.created_at).toLocaleDateString()}
              </p>
              {project.description && (
                <p className="settings-info">
                  Description: {project.description}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
