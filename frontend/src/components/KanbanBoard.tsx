import { useState, useEffect } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { api } from '../api/client';
import type { Task, TaskStatus, Project, PersonBrief, ProjectWithDetails } from '../types';
import { KanbanColumn } from './KanbanColumn';
import { TaskDrawer } from './TaskDrawer';
import { TaskCard } from './TaskCard';
import { ProjectSettings } from './ProjectSettings';

const COLUMNS: { status: TaskStatus; title: string }[] = [
  { status: 'NOT_STARTED', title: 'To Do' },
  { status: 'PLANNING', title: 'Planning' },
  { status: 'DEVELOPMENT', title: 'In Progress' },
  { status: 'TESTING', title: 'Testing' },
  { status: 'FINISHED', title: 'Done' },
];

interface Props {
  project: Project;
}

export function KanbanBoard({ project }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [newTaskName, setNewTaskName] = useState('');
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [filters, setFilters] = useState<{
    status?: TaskStatus;
    assignee_id?: number;
    severity?: number;
  }>({});
  const [members, setMembers] = useState<PersonBrief[]>([]);
  const [projectDetails, setProjectDetails] = useState<ProjectWithDetails | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

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
    setProjectDetails(projectData);
    setMembers(projectData.members.map((m) => m.person));
  };

  const handleDragStart = (event: DragStartEvent) => {
    const task = tasks.find((t) => t.task_id === event.active.id);
    if (task) {
      setActiveTask(task);
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeTaskId = active.id as number;
    const overId = over.id;

    const activeTask = tasks.find((t) => t.task_id === activeTaskId);
    if (!activeTask) return;

    // Check if dropping over a column
    const overColumn = COLUMNS.find((c) => c.status === overId);
    if (overColumn && activeTask.status !== overColumn.status) {
      setTasks((tasks) =>
        tasks.map((t) =>
          t.task_id === activeTaskId ? { ...t, status: overColumn.status } : t
        )
      );
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const taskId = active.id as number;
    const task = tasks.find((t) => t.task_id === taskId);
    if (!task) return;

    // Find the target status
    let targetStatus: TaskStatus | null = null;
    const overColumn = COLUMNS.find((c) => c.status === over.id);
    if (overColumn) {
      targetStatus = overColumn.status;
    } else {
      // Dropped over another task, find its status
      const overTask = tasks.find((t) => t.task_id === over.id);
      if (overTask) {
        targetStatus = overTask.status;
      }
    }

    if (targetStatus && task.status !== targetStatus) {
      try {
        await api.updateTask(taskId, { status: targetStatus });
      } catch {
        loadTasks();
      }
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
    setSelectedTask(task);
  };

  const handleTaskClick = (task: Task) => {
    if (!activeTask) {
      setSelectedTask(task);
    }
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

  const clearFilters = () => {
    setFilters({});
  };

  const hasFilters = filters.assignee_id || filters.severity;

  return (
    <div className="kanban-container">
      <div className="kanban-header">
        <div className="kanban-header-left">
          <h1>{project.name}</h1>
          {project.description && (
            <p className="project-description">{project.description}</p>
          )}
        </div>
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

          {hasFilters && (
            <button className="btn-secondary" onClick={clearFilters}>
              Clear Filters
            </button>
          )}

          <button className="btn-primary" onClick={() => setShowCreate(true)}>
            + Create Task
          </button>
          <button className="btn-secondary" onClick={() => setShowSettings(true)}>
            Settings
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
                placeholder="What needs to be done?"
                value={newTaskName}
                onChange={(e) => setNewTaskName(e.target.value)}
                autoFocus
              />
              <div className="form-actions">
                <button type="submit" className="btn-primary">Create</button>
                <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>
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
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="kanban-board">
            {COLUMNS.map((column) => (
              <KanbanColumn
                key={column.status}
                status={column.status}
                title={column.title}
                tasks={getTasksByStatus(column.status)}
                onTaskClick={handleTaskClick}
              />
            ))}
          </div>
          <DragOverlay>
            {activeTask ? (
              <TaskCard
                task={activeTask}
                onClick={() => {}}
                isDragOverlay
              />
            ) : null}
          </DragOverlay>
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

      {showSettings && projectDetails && (
        <ProjectSettings
          project={projectDetails}
          onClose={() => setShowSettings(false)}
          onUpdate={() => {
            loadProjectMembers();
          }}
        />
      )}
    </div>
  );
}
