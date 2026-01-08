import { useState } from 'react';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { Login } from './components/Login';
import { ProjectList } from './components/ProjectList';
import { KanbanBoard } from './components/KanbanBoard';
import type { Project } from './types';
import './App.css';

function AppContent() {
  const { user, loading, logout } = useAuth();
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">Tasker</div>
        <div className="user-menu">
          <span>{user.name}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      <div className="app-body">
        <ProjectList
          onSelectProject={setSelectedProject}
          selectedProjectId={selectedProject?.project_id}
        />

        <main className="main-content">
          {selectedProject ? (
            <KanbanBoard project={selectedProject} />
          ) : (
            <div className="empty-state">
              <h2>Welcome to Tasker</h2>
              <p>Select a project or create a new one to get started</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
