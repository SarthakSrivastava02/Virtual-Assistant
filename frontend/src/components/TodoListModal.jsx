import React, { useState, useEffect } from 'react';

export default function TodoListModal({ isOpen, onClose, onTodosUpdated }) {
  const [todos, setTodos] = useState([]);
  const [newTask, setNewTask] = useState('');
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all'); // all, active, completed

  useEffect(() => {
    if (isOpen) {
      loadTodos();
    }
  }, [isOpen]);

  const loadTodos = async () => {
    setLoading(true);
    try {
      const res = await fetch('/todos');
      if (res.ok) {
        const data = await res.json();
        setTodos(data);
      }
    } catch (e) {
      console.error("Failed to load todos:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newTask.trim()) return;
    try {
      const res = await fetch('/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: newTask.trim() }),
      });
      if (res.ok) {
        setNewTask('');
        loadTodos();
        if (onTodosUpdated) onTodosUpdated();
      }
    } catch (e) {
      console.error("Failed to add todo:", e);
    }
  };

  const handleToggle = async (todoId, currentStatus) => {
    try {
      const res = await fetch(`/todos/${todoId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: !currentStatus }),
      });
      if (res.ok) {
        loadTodos();
        if (onTodosUpdated) onTodosUpdated();
      }
    } catch (e) {
      console.error("Failed to toggle todo:", e);
    }
  };

  const handleDelete = async (todoId) => {
    try {
      const res = await fetch(`/todos/${todoId}`, { method: 'DELETE' });
      if (res.ok) {
        loadTodos();
        if (onTodosUpdated) onTodosUpdated();
      }
    } catch (e) {
      console.error("Failed to delete todo:", e);
    }
  };

  if (!isOpen) return null;

  const filtered = todos.filter(t => {
    if (filter === 'active') return !t.completed;
    if (filter === 'completed') return t.completed;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 text-slate-800 dark:text-slate-100 max-h-[85vh] flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2.5">
            <span className="text-xl">📝</span>
            <div>
              <h2 className="text-base font-semibold">Study & Project Task Manager</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Integrated SQLite task storage & natural language execution</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-md"
          >
            ✕
          </button>
        </div>

        {/* Add Input */}
        <form onSubmit={handleAdd} className="flex gap-2 py-4 border-b border-slate-100 dark:border-slate-800">
          <input
            type="text"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            placeholder="Add new task (e.g., Review Unit 4 Paging)..."
            className="flex-1 px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-sm shadow-blue-500/20 transition-colors"
          >
            Add
          </button>
        </form>

        {/* Filters */}
        <div className="flex items-center space-x-2 py-2 text-[11px] font-medium text-slate-500 dark:text-slate-400">
          <span>Filter:</span>
          {['all', 'active', 'completed'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 rounded-md capitalize transition-colors ${
                filter === f ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400 font-semibold' : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Task List */}
        <div className="flex-1 overflow-y-auto py-2 space-y-1.5 text-xs">
          {loading ? (
            <div className="py-8 text-center text-slate-400">Loading tasks...</div>
          ) : filtered.length === 0 ? (
            <div className="py-8 text-center text-slate-400">No tasks in this view.</div>
          ) : (
            filtered.map((todo) => (
              <div
                key={todo.id}
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 hover:border-slate-300 transition-all"
              >
                <div className="flex items-center space-x-2.5 flex-1 min-w-0 pr-2">
                  <input
                    type="checkbox"
                    checked={todo.completed}
                    onChange={() => handleToggle(todo.id, todo.completed)}
                    className="w-4 h-4 rounded text-blue-600 focus:ring-0 cursor-pointer"
                  />
                  <span className={`truncate ${todo.completed ? 'line-through text-slate-400' : 'text-slate-800 dark:text-slate-200'}`}>
                    {todo.task}
                  </span>
                </div>
                <button
                  onClick={() => handleDelete(todo.id)}
                  className="text-slate-400 hover:text-red-500 p-1 rounded transition-colors"
                  title="Delete task"
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>{todos.filter(t => t.completed).length} of {todos.length} completed</span>
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
