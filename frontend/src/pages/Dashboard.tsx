import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

interface Todo {
  _id: string;
  title: string;
  priority: 'low' | 'medium' | 'high';
  completed: boolean;
  createdAt: string;
}

type Filter = 'all' | 'low' | 'medium' | 'high';

const PRIORITY_LABELS = { low: 'Low', medium: 'Medium', high: 'High' };

const PriorityBadge: React.FC<{ priority: 'low' | 'medium' | 'high' }> = ({ priority }) => (
  <span className={`badge badge-${priority}`} aria-label={`Priority: ${PRIORITY_LABELS[priority]}`}>
    {priority === 'high' && '🔴'} {priority === 'medium' && '🟡'} {priority === 'low' && '🟢'}
    {PRIORITY_LABELS[priority]}
  </span>
);

const Dashboard: React.FC = () => {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [filter, setFilter] = useState<Filter>('all');
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const navigate = useNavigate();

  const fetchTodos = useCallback(async () => {
    try {
      const response = await api.get('/todos');
      setTodos(response.data);
    } catch (error: any) {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchTodos();
  }, [fetchTodos]);

  const handleAddTodo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setAdding(true);
    try {
      const response = await api.post('/todos', { title: title.trim(), priority });
      setTodos(prev => [response.data, ...prev]);
      setTitle('');
    } finally {
      setAdding(false);
    }
  };

  const toggleComplete = async (id: string, currentStatus: boolean) => {
    try {
      const response = await api.patch(`/todos/${id}`, { completed: !currentStatus });
      setTodos(prev => prev.map(t => (t._id === id ? response.data : t)));
    } catch {
      // revert optimistic update handled by re-fetch
    }
  };

  const deleteTodo = async (id: string) => {
    // Optimistic removal
    setTodos(prev => prev.filter(t => t._id !== id));
    try {
      await api.delete(`/todos/${id}`);
    } catch {
      fetchTodos(); // revert on error
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const filteredTodos = todos.filter(t => filter === 'all' || t.priority === filter);
  const completedCount = todos.filter(t => t.completed).length;
  const pendingCount = todos.filter(t => !t.completed).length;

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <a href="#main" className="header-logo" aria-label="Taskly home">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
            </svg>
            Taskly
          </a>
          <div className="header-actions">
            <button onClick={handleLogout} className="btn btn-secondary" aria-label="Log out">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              Log out
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main id="main" className="dashboard-main">

        {/* Stats */}
        <div className="stats-row" role="region" aria-label="Task summary">
          <div className="stat-card">
            <span className="stat-value">{todos.length}</span>
            <span className="stat-label">Total tasks</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{pendingCount}</span>
            <span className="stat-label">Pending</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{completedCount}</span>
            <span className="stat-label">Completed</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">
              {todos.length > 0 ? Math.round((completedCount / todos.length) * 100) : 0}%
            </span>
            <span className="stat-label">Progress</span>
          </div>
        </div>

        {/* Add Todo */}
        <div className="add-todo-card" role="region" aria-label="Add new task">
          <p className="add-todo-title">New task</p>
          <form onSubmit={handleAddTodo}>
            <div className="add-todo-row">
              <div className="form-group input-wrapper">
                <label htmlFor="todo-title" className="form-label">Task title</label>
                <input
                  id="todo-title"
                  type="text"
                  className="form-input"
                  placeholder="What needs to be done?"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  autoComplete="off"
                />
              </div>
              <div className="form-group select-wrapper">
                <label htmlFor="todo-priority" className="form-label">Priority</label>
                <select
                  id="todo-priority"
                  className="form-select"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high')}
                >
                  <option value="low">🟢 Low</option>
                  <option value="medium">🟡 Medium</option>
                  <option value="high">🔴 High</option>
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0, alignSelf: 'flex-end' }}>
                <label className="form-label" style={{ visibility: 'hidden' }}>Add</label>
                <button type="submit" className="btn-add" disabled={adding || !title.trim()}>
                  {adding
                    ? <span className="spinner" aria-hidden="true" style={{ borderTopColor: '#fff', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff' }} />
                    : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                      </svg>
                    )
                  }
                  Add task
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Filter Tabs */}
        <div className="filter-bar" role="group" aria-label="Filter tasks by priority">
          <span className="filter-label">Filter:</span>
          {(['all', 'high', 'medium', 'low'] as Filter[]).map(f => (
            <button
              key={f}
              className={`filter-btn${filter === f ? ' active' : ''}`}
              onClick={() => setFilter(f)}
              aria-pressed={filter === f}
            >
              {f === 'all' ? 'All' : PRIORITY_LABELS[f]}
              {f !== 'all' && (
                <span style={{ marginLeft: 4, opacity: 0.7 }}>
                  ({todos.filter(t => t.priority === f).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Todo List */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--color-text-muted)' }}>
            Loading tasks…
          </div>
        ) : filteredTodos.length === 0 ? (
          <div className="empty-state" role="status">
            <span className="empty-state-icon">
              {filter === 'all' ? '✅' : '🔍'}
            </span>
            <p className="empty-state-title">
              {filter === 'all' ? 'No tasks yet' : `No ${filter} priority tasks`}
            </p>
            <p className="empty-state-desc">
              {filter === 'all'
                ? 'Add your first task above to get started.'
                : 'Try a different filter or add a new task.'}
            </p>
          </div>
        ) : (
          <ul className="todo-list" aria-label="Task list">
            {filteredTodos.map(todo => (
              <li key={todo._id} className={`todo-item${todo.completed ? ' completed' : ''}`}>
                <input
                  type="checkbox"
                  className="todo-checkbox"
                  checked={todo.completed}
                  onChange={() => toggleComplete(todo._id, todo.completed)}
                  aria-label={`Mark "${todo.title}" as ${todo.completed ? 'incomplete' : 'complete'}`}
                />
                <div className="todo-content">
                  <p className="todo-title">{todo.title}</p>
                  <div className="todo-meta">
                    <PriorityBadge priority={todo.priority} />
                  </div>
                </div>
                <div className="todo-actions">
                  <button
                    className="btn-delete"
                    onClick={() => deleteTodo(todo._id)}
                    aria-label={`Delete task: ${todo.title}`}
                    title="Delete task"
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
                    </svg>
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
