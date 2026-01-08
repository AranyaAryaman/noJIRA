import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Task } from '../types';

interface Props {
  task: Task;
  onClick: () => void;
  isDragOverlay?: boolean;
}

const priorityColors: Record<number, string> = {
  1: '#94a3b8',
  2: '#0065ff',
  3: '#fbbf24',
  4: '#fb923c',
  5: '#ef4444',
};

export function TaskCard({ task, onClick, isDragOverlay }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: task.task_id,
    data: { task },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    cursor: isDragOverlay ? 'grabbing' : 'grab',
  };

  const handleClick = (e: React.MouseEvent) => {
    if (isDragging) return;
    e.stopPropagation();
    onClick();
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`task-card ${isDragOverlay ? 'dragging' : ''}`}
      onClick={handleClick}
      {...attributes}
      {...listeners}
    >
      <div className="task-card-header">
        <span
          className="priority-indicator"
          style={{ backgroundColor: priorityColors[task.priority] }}
          title={`Priority ${task.priority}`}
        />
        <span className="task-id">TASK-{task.task_id}</span>
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
