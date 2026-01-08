import { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { Task, Comment, PersonBrief, TaskStatus } from '../types';

interface Props {
  task: Task;
  members: PersonBrief[];
  onClose: () => void;
  onUpdate: (task: Task) => void;
  onDelete: (taskId: number) => void;
}

const STATUSES: TaskStatus[] = ['NOT_STARTED', 'PLANNING', 'DEVELOPMENT', 'TESTING', 'FINISHED'];

export function TaskDrawer({ task, members, onClose, onUpdate, onDelete }: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: task.name,
    description: task.description || '',
    assignee_id: task.assignee_id || 0,
    status: task.status,
    severity: task.severity,
    priority: task.priority,
    tags: task.tags.map((t) => t.tag).join(', '),
  });

  useEffect(() => {
    loadComments();
  }, [task.task_id]);

  const loadComments = async () => {
    const data = await api.listComments(task.task_id);
    setComments(data);
  };

  const handleSave = async () => {
    const updated = await api.updateTask(task.task_id, {
      name: editForm.name,
      description: editForm.description || undefined,
      assignee_id: editForm.assignee_id || null,
      status: editForm.status,
      severity: editForm.severity,
      priority: editForm.priority,
      tags: editForm.tags.split(',').map((t) => t.trim()).filter(Boolean),
    });
    onUpdate(updated);
    setEditing(false);
  };

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this task?')) {
      await api.deleteTask(task.task_id);
      onDelete(task.task_id);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    const comment = await api.createComment(task.task_id, newComment);
    setComments([...comments, comment]);
    setNewComment('');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    await api.uploadTaskAttachment(task.task_id, file);
    const updated = await api.getTask(task.task_id);
    onUpdate(updated);
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <h2>Task #{task.task_id}</h2>
          <div className="drawer-actions">
            {!editing && (
              <button onClick={() => setEditing(true)}>Edit</button>
            )}
            <button className="btn-danger" onClick={handleDelete}>
              Delete
            </button>
            <button onClick={onClose}>Close</button>
          </div>
        </div>

        <div className="drawer-content">
          {editing ? (
            <div className="edit-form">
              <label>
                Name
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </label>

              <label>
                Description
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  rows={4}
                />
              </label>

              <div className="form-row">
                <label>
                  Status
                  <select
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value as TaskStatus })}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s.replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Assignee
                  <select
                    value={editForm.assignee_id}
                    onChange={(e) => setEditForm({ ...editForm, assignee_id: Number(e.target.value) })}
                  >
                    <option value={0}>Unassigned</option>
                    {members.map((m) => (
                      <option key={m.person_id} value={m.person_id}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="form-row">
                <label>
                  Priority (1-5)
                  <select
                    value={editForm.priority}
                    onChange={(e) => setEditForm({ ...editForm, priority: Number(e.target.value) })}
                  >
                    {[1, 2, 3, 4, 5].map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Severity (1-5)
                  <select
                    value={editForm.severity}
                    onChange={(e) => setEditForm({ ...editForm, severity: Number(e.target.value) })}
                  >
                    {[1, 2, 3, 4, 5].map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <label>
                Tags (comma-separated)
                <input
                  type="text"
                  value={editForm.tags}
                  onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                  placeholder="bug, frontend, urgent"
                />
              </label>

              <div className="form-actions">
                <button onClick={handleSave}>Save</button>
                <button onClick={() => setEditing(false)}>Cancel</button>
              </div>
            </div>
          ) : (
            <>
              <h3>{task.name}</h3>
              <p className="description">{task.description || 'No description'}</p>

              <div className="task-meta">
                <div className="meta-item">
                  <span className="label">Status</span>
                  <span className="value">{task.status.replace('_', ' ')}</span>
                </div>
                <div className="meta-item">
                  <span className="label">Assignee</span>
                  <span className="value">{task.assignee?.name || 'Unassigned'}</span>
                </div>
                <div className="meta-item">
                  <span className="label">Priority</span>
                  <span className="value">{task.priority}</span>
                </div>
                <div className="meta-item">
                  <span className="label">Severity</span>
                  <span className="value">{task.severity}</span>
                </div>
                <div className="meta-item">
                  <span className="label">Created</span>
                  <span className="value">
                    {new Date(task.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {task.tags.length > 0 && (
                <div className="task-tags">
                  {task.tags.map((t) => (
                    <span key={t.tag} className="tag">
                      {t.tag}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}

          <div className="attachments-section">
            <h4>Attachments ({task.attachments.length})</h4>
            <input type="file" onChange={handleFileUpload} />
            <ul className="attachment-list">
              {task.attachments.map((a) => (
                <li key={a.attachment_id}>
                  <a
                    href={api.downloadTaskAttachment(a.attachment_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {a.file_name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div className="comments-section">
            <h4>Comments ({comments.length})</h4>

            <form onSubmit={handleAddComment} className="comment-form">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                rows={2}
              />
              <button type="submit">Add Comment</button>
            </form>

            <div className="comment-list">
              {comments.map((comment) => (
                <div
                  key={comment.comment_id}
                  className={`comment ${comment.is_system_comment ? 'system' : ''}`}
                >
                  <div className="comment-header">
                    <span className="author">{comment.person?.name || 'System'}</span>
                    <span className="date">
                      {new Date(comment.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p>{comment.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
