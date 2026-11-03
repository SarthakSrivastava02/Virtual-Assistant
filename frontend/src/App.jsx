import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import FileUpload from './components/FileUpload';
import Settings from './components/Settings';
import KnowledgeAssistant from './components/KnowledgeAssistant';
import TodoListModal from './components/TodoListModal';
import LoginPage from './components/LoginPage';

export default function App() {
  // Authentication State
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Conversations State
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);

  // Modals & Drawers
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isKnowledgeOpen, setIsKnowledgeOpen] = useState(false);
  const [isTodosOpen, setIsTodosOpen] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Knowledge / RAG state
  const [useRag, setUseRag] = useState(true);
  const [strictRag, setStrictRag] = useState(false);
  const [focusedDoc, setFocusedDoc] = useState(null);
  const [documentsCount, setDocumentsCount] = useState(0);
  const [todosCount, setTodosCount] = useState(0);
  const [systemStatus, setSystemStatus] = useState(null);

  // Initialize session & theme
  useEffect(() => {
    // Theme preference
    const savedTheme = localStorage.getItem('va_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialDark = savedTheme ? savedTheme === 'dark' : prefersDark;
    setIsDarkMode(initialDark);
    if (initialDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Check user auth token
    const savedToken = localStorage.getItem('va_token');
    const savedUser = localStorage.getItem('va_user');
    if (savedToken && savedUser) {
      try {
        setCurrentUser(JSON.parse(savedUser));
        setToken(savedToken);
      } catch (e) {
        localStorage.removeItem('va_token');
        localStorage.removeItem('va_user');
      }
    }
    setAuthChecked(true);
  }, []);

  // When user is authenticated, load initial data
  useEffect(() => {
    if (currentUser) {
      loadInitialData();
    }
  }, [currentUser]);

  const loadInitialData = async () => {
    await fetchConversations();
    await fetchSystemHealth();
    await fetchTodosCount();
  };

  const handleLoginSuccess = (user, authToken) => {
    setCurrentUser(user);
    setToken(authToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('va_token');
    localStorage.removeItem('va_user');
    setCurrentUser(null);
    setToken(null);
    setConversations([]);
    setMessages([]);
    setActiveConvId(null);
  };

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('va_theme', newTheme ? 'dark' : 'light');
    if (newTheme) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
        setDocumentsCount(data.documents_count || 0);
      }
    } catch (e) {
      console.error("Health check error:", e);
    }
  };

  const fetchTodosCount = async () => {
    try {
      const res = await fetch('/todos');
      if (res.ok) {
        const data = await res.json();
        setTodosCount(data.length);
      }
    } catch (e) {
      console.error("Todos fetch error:", e);
    }
  };

  const fetchConversations = async () => {
    try {
      const url = currentUser ? `/history?user_id=${currentUser.id}` : '/history';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
        if (data.length > 0 && !activeConvId) {
          selectConversation(data[0].id);
        }
      }
    } catch (e) {
      console.error("Error loading conversations:", e);
    }
  };

  const selectConversation = async (convId) => {
    setActiveConvId(convId);
    try {
      const res = await fetch(`/history/${convId}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (e) {
      console.error("Error fetching chat details:", e);
    }
  };

  const handleNewChat = async () => {
    try {
      const url = currentUser ? `/new-chat?user_id=${currentUser.id}` : '/new-chat';
      const res = await fetch(url, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setActiveConvId(data.conversation_id);
        setMessages([]);
        setFocusedDoc(null);
        await fetchConversations();
      }
    } catch (e) {
      console.error("Error creating new chat:", e);
    }
  };

  const handleDeleteChat = async (convId) => {
    try {
      const res = await fetch(`/conversations/${convId}`, { method: 'DELETE' });
      if (res.ok) {
        const remaining = conversations.filter(c => c.id !== convId);
        setConversations(remaining);
        if (activeConvId === convId) {
          if (remaining.length > 0) {
            selectConversation(remaining[0].id);
          } else {
            setActiveConvId(null);
            setMessages([]);
          }
        }
      }
    } catch (e) {
      console.error("Error deleting conversation:", e);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm("Are you sure you want to clear your conversation history?")) return;
    try {
      const url = currentUser ? `/clear-history?user_id=${currentUser.id}` : '/clear-history';
      const res = await fetch(url, { method: 'DELETE' });
      if (res.ok) {
        setConversations([]);
        setActiveConvId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error("Error clearing history:", e);
    }
  };

  const handleSendMessage = async (userText) => {
    if (!userText.trim()) return;

    // Optimistically append user message to UI
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: userText,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const payload = {
        message: userText,
        conversation_id: activeConvId,
        use_rag: useRag,
        document_id: focusedDoc ? focusedDoc.id : null,
        strict_rag: strictRag,
        user_id: currentUser ? currentUser.id : 1
      };

      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to generate response');
      }

      const data = await res.json();

      if (!activeConvId && data.conversation_id) {
        setActiveConvId(data.conversation_id);
      }

      const assistantMsg = {
        id: data.message_id,
        role: 'assistant',
        content: data.response,
        sources: data.sources || [],
        created_at: data.timestamp
      };
      setMessages(prev => [...prev, assistantMsg]);

      fetchConversations();
      fetchTodosCount();

    } catch (err) {
      const errorMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `⚠️ **Error:** ${err.message}`,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartChatWithDoc = (doc) => {
    setFocusedDoc(doc);
    setUseRag(true);
    setStrictRag(true);
    handleNewChat();
  };

  // If session is still loading
  if (!authChecked) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-900 text-white">
        <span className="animate-spin text-2xl mr-2">⚡</span> Loading session...
      </div>
    );
  }

  // If not logged in, show Login Screen
  if (!currentUser) {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        isDarkMode={isDarkMode}
        onToggleTheme={toggleTheme}
      />
    );
  }

  const activeConversation = conversations.find(c => c.id === activeConvId);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-slate-950 font-sans">
      
      {/* Sidebar Navigation */}
      <Sidebar
        conversations={conversations}
        activeId={activeConvId}
        onSelectChat={selectConversation}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onClearHistory={handleClearHistory}
        onOpenKnowledge={() => setIsKnowledgeOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenTodos={() => setIsTodosOpen(true)}
        documentsCount={documentsCount}
        todosCount={todosCount}
        isDarkMode={isDarkMode}
        onToggleTheme={toggleTheme}
        isOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Main Chat Interface */}
      <ChatWindow
        conversation={activeConversation}
        messages={messages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
        onOpenUpload={() => setIsUploadOpen(true)}
        useRag={useRag}
        onToggleRag={() => setUseRag(!useRag)}
        strictRag={strictRag}
        onToggleStrictRag={() => setStrictRag(!strictRag)}
        onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        focusedDoc={focusedDoc}
        onClearFocusDoc={() => setFocusedDoc(null)}
        systemStatus={systemStatus}
        currentUser={currentUser}
      />

      {/* Modals & Dialogs */}
      <FileUpload
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={(doc) => {
          fetchSystemHealth();
          setUseRag(true);
        }}
      />

      <Settings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSettingsUpdated={fetchSystemHealth}
      />

      <KnowledgeAssistant
        isOpen={isKnowledgeOpen}
        onClose={() => setIsKnowledgeOpen(false)}
        onOpenUpload={() => setIsUploadOpen(true)}
        onStartChatWithDoc={handleStartChatWithDoc}
      />

      <TodoListModal
        isOpen={isTodosOpen}
        onClose={() => setIsTodosOpen(false)}
        onTodosUpdated={fetchTodosCount}
      />
    </div>
  );
}
