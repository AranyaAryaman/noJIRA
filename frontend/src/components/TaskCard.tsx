import { useDraggable } from '@dnd-kit/core';
import type { Task } from '../types';

interface Props {
  task: Task;
  onClick: () => void;
}

const priorityColors: Record<number, string> = {
  1: '#94a3b8',
  2: '#60a5fa',
  3: '#fbbf24',
  4: '#fb923c',
  5: '#ef4444',
};

export function TaskCard({ task, onClick }: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: task.task_id,
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.5 : 1,
      }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="task-card"
      onClick={onClick}
    >
      <div className="task-card-header">
        <span
          className="priority-indicator"
          style={{ backgroundColor: priorityColors[task.priority] }}
          title={`Priority ${task.priority}`}
        />
        <span className="task-id">#{task.task_id}</span>
      </div>
      <h4 className="task-name">{task.name}</h4>
      <div className="task-card-footer">
        {task.assignee && (
          <span className="assignee" title={task.assignee.name}>
            {task.assignee.name.charAt(0).toUpperCase()}
          </span>
        )}
        {task.tags.length > 0 && (
          <div className="tags">
            {task.tags.slice(0, 2).map((t) => (
              <span key={t.tag} className="tag">
                {t.tag}
              </span>
            ))}
            {task.tags.length > 2 && (
              <span className="tag">+{task.tags.length - 2}</span>
            )}
          </div>
        )}
        {task.due_date && (
          <span className="due-date">
            {new Date(task.due_date).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}
