import { useState, useEffect } from 'react';
import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core';
import { api } from '../api/client';
import type { Task, TaskStatus, Project, PersonBrief } from '../types';
import { KanbanColumn } from './KanbanColumn';
import { TaskDrawer } from './TaskDrawer';

const COLUMNS: { status: TaskStatus; title: string }[] = [
  { status: 'NOT_STARTED', title: 'Not Started' },
  { status: 'PLANNING', title: 'Planning' },
  { status: 'DEVELOPMENT', title: 'Development' },
  { status: 'TESTING', title: 'Testing' },
  { status: 'FINISHED', title: 'Finished' },
];

interface Props {
  project: Project;
}

export function KanbanBoard({ project }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newTaskName, setNewTaskName] = useState('');
  const [filters, setFilters] = useState<{
    status?: TaskStatus;
    assignee_id?: number;
    severity?: number;
  }>({});
  const [members, setMembers] = useState<PersonBrief[]>([]);

  useEffect(() => {
    loadTasks();
    loadProjectMembers();
  }, [project.project_id, filters]);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await api.listTasks(project.project_id, filters);
      setTasks(data);
    } finally {
      setLoading(false);
    }
  };

  const loadProjectMembers = async () => {
    const projectData = await api.getProject(project.project_id);
    setMembers(projectData.members.map((m) => m.person));
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const taskId = Number(active.id);
    const newStatus = over.id as TaskStatus;

    const task = tasks.find((t) => t.task_id === taskId);
    if (!task || task.status === newStatus) return;

    // Optimistic update
    setTasks(tasks.map((t) =>
      t.task_id === taskId ? { ...t, status: newStatus } : t
    ));

    try {
      await api.updateTask(taskId, { status: newStatus });
    } catch {
      // Revert on error
      loadTasks();
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskName.trim()) return;

    const task = await api.createTask({
      project_id: project.project_id,
      name: newTaskName,
    });
    setTasks([...tasks, task]);
    setNewTaskName('');
    setShowCreate(false);
  };

  const handleTaskUpdate = (updatedTask: Task) => {
    setTasks(tasks.map((t) =>
      t.task_id === updatedTask.task_id ? updatedTask : t
    ));
    setSelectedTask(updatedTask);
  };

  const handleTaskDelete = (taskId: number) => {
    setTasks(tasks.filter((t) => t.task_id !== taskId));
    setSelectedTask(null);
  };

  const getTasksByStatus = (status: TaskStatus) =>
    tasks.filter((t) => t.status === status);

  return (
    <div className="kanban-container">
      <div className="kanban-header">
        <h1>{project.name}</h1>
        <div className="kanban-actions">
          <select
            value={filters.assignee_id || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                assignee_id: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          >
            <option value="">All Assignees</option>
            {members.map((m) => (
              <option key={m.person_id} value={m.person_id}>
                {m.name}
              </option>
            ))}
          </select>

          <select
            value={filters.severity || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                severity: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          >
            <option value="">All Severities</option>
            {[1, 2, 3, 4, 5].map((s) => (
              <option key={s} value={s}>
                Severity {s}
              </option>
            ))}
          </select>

          <button className="btn-primary" onClick={() => setShowCreate(true)}>
            + New Task
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create Task</h2>
            <form onSubmit={handleCreateTask}>
              <input
                type="text"
                placeholder="Task name"
                value={newTaskName}
                onChange={(e) => setNewTaskName(e.target.value)}
                autoFocus
              />
              <div className="form-actions">
                <button type="submit">Create</button>
                <button type="button" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading tasks...</div>
      ) : (
        <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <div className="kanban-board">
            {COLUMNS.map((column) => (
              <KanbanColumn
                key={column.status}
                status={column.status}
                title={column.title}
                tasks={getTasksByStatus(column.status)}
                onTaskClick={setSelectedTask}
              />
            ))}
          </div>
        </DndContext>
      )}

      {selectedTask && (
        <TaskDrawer
          task={selectedTask}
          members={members}
          onClose={() => setSelectedTask(null)}
          onUpdate={handleTaskUpdate}
          onDelete={handleTaskDelete}
        />
      )}
    </div>
  );
}
