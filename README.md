# Tasker

Local-first task tracking for small teams. A lightweight, open-source alternative to Jira.

## Features

- **Projects** - Create and manage projects with team assignments
- **Kanban Board** - Drag-and-drop task management with status columns
- **Tasks** - Full task lifecycle with assignees, priorities, tags, and subtasks
- **Comments** - Discussion threads with automatic system comments for changes
- **Attachments** - File uploads for tasks and comments
- **Teams** - Organize people into teams with role-based access

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd tasker

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy, Alembic
- **Database**: PostgreSQL
- **Frontend**: React, TypeScript, dnd-kit
- **Auth**: JWT (email-based login)
- **Storage**: Local filesystem
- **Infrastructure**: Docker, docker-compose

## Project Structure

```
tasker/
├── backend/
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks
│   │   ├── api/         # API client
│   │   └── types/       # TypeScript types
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## API Endpoints

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT)
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project details
- `PATCH /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/members` - Add member
- `POST /api/projects/{id}/teams` - Assign team

### Teams
- `GET /api/teams` - List teams
- `POST /api/teams` - Create team
- `GET /api/teams/{id}` - Get team with members
- `PATCH /api/teams/{id}` - Update team
- `DELETE /api/teams/{id}` - Delete team
- `POST /api/teams/{id}/members` - Add member

### Tasks
- `GET /api/tasks?project_id={id}` - List tasks (with filters)
- `POST /api/tasks` - Create task
- `GET /api/tasks/{id}` - Get task details
- `PATCH /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Comments
- `GET /api/comments/task/{task_id}` - List comments
- `POST /api/comments` - Create comment
- `PATCH /api/comments/{id}` - Update comment
- `DELETE /api/comments/{id}` - Delete comment

### Attachments
- `POST /api/attachments/task/{task_id}` - Upload task attachment
- `GET /api/attachments/task/{id}/download` - Download attachment
- `DELETE /api/attachments/task/{id}` - Delete attachment

## Development

### Backend Only

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL (e.g., via Docker)
docker run -d --name postgres -e POSTGRES_PASSWORD=tasker -e POSTGRES_USER=tasker -e POSTGRES_DB=tasker -p 5432:5432 postgres:15-alpine

# Run migrations
DATABASE_URL=postgresql://tasker:tasker@localhost:5432/tasker alembic upgrade head

# Start server
DATABASE_URL=postgresql://tasker:tasker@localhost:5432/tasker uvicorn app.main:app --reload
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

## Task Status Flow

```
NOT_STARTED → PLANNING → DEVELOPMENT → TESTING → FINISHED
```

## Permissions

### Project Roles
- **ADMIN** - Full access, can manage members
- **MEMBER** - Can create/edit tasks
- **VIEWER** - Read-only access

### Team Roles
- **OWNER** - Can manage team
- **MEMBER** - Basic team member

Team members get MEMBER-level access to projects their team is assigned to.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `tasker` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `tasker` |
| `POSTGRES_DB` | PostgreSQL database | `tasker` |
| `SECRET_KEY` | JWT signing key | (required in production) |
| `DATABASE_URL` | Full database URL | Built from above |

## License

MIT
