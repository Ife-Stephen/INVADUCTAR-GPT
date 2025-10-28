'use client'

import { useState, useEffect } from 'react';
import Header from '../components/Header';
import ChatMessage from '../components/ChatMessage';
import TypingIndicator from '../components/TypingIndicator';
import ImageUpload from '../components/ImageUpload';

interface Message {
  id: number;
  message: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

// API URL configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, message: "Hello! I'm INVADUCTAR GPT, your specialized assistant for invasive ductal carcinoma information. I can help you understand breast cancer diagnosis, treatment options, and provide support. How can I assist you today?", isUser: false, timestamp: new Date() }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [copyrightExpanded, setCopyrightExpanded] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [privacyExpanded, setPrivacyExpanded] = useState(false);

  // Load conversation on mount
  useEffect(() => {
    loadConversation();
  }, []);

  const loadConversation = async () => {
    try {
      const response = await fetch(`${API_URL}/api/conversation`);
      const data = await response.json();
      
      if (data.success && data.messages.length > 0) {
        const formattedMessages = data.messages
          .filter((msg: any) => msg.message && msg.message.trim()) // Filter out empty messages
          .map((msg: any, index: number) => ({
            id: index + 1,
            message: msg.message,
            isUser: msg.isUser,
            timestamp: new Date(msg.timestamp)
          }));
        
        // Only update if we have valid messages
        if (formattedMessages.length > 0) {
          setMessages(formattedMessages);
        }
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const createNewSession = (firstMessage: string) => {
    const sessionId = Date.now().toString();
    const title = firstMessage.substring(0, 40) + (firstMessage.length > 40 ? '...' : '');
    
    const newSession: ChatSession = {
      id: sessionId,
      title,
      timestamp: new Date(),
      messages: []
    };
    
    setChatSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(sessionId);
    return sessionId;
  };

  const handleNewConsultation = () => {
    setMessages([
      { id: 1, message: "Hello! I'm INVADUCTAR GPT, your specialized assistant for invasive ductal carcinoma information. I can help you understand breast cancer diagnosis, treatment options, and provide support. How can I assist you today?", isUser: false, timestamp: new Date() }
    ]);
    setCurrentSessionId(null);
  };

  const handleClearAllData = async () => {
    if (!confirm('⚠️ This will permanently delete all your chat history and data from our servers. Are you sure?')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/clear-conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Clear local state
        setMessages([
          { id: 1, message: "Hello! I'm INVADUCTAR GPT, your specialized assistant for invasive ductal carcinoma information. I can help you understand breast cancer diagnosis, treatment options, and provide support. How can I assist you today?", isUser: false, timestamp: new Date() }
        ]);
        setChatSessions([]);
        setCurrentSessionId(null);
        
        alert('✅ All your data has been permanently deleted from our servers.');
      } else {
        throw new Error(data.error || 'Failed to clear data');
      }
    } catch (error: unknown) {
      console.error('Clear data error:', error);

      if (error instanceof TypeError && error.message.includes('fetch')) {
        alert(`❌ Cannot connect to server. Please make sure the backend is running at ${API_URL}`);
      } else if (error instanceof Error) {
        alert(`❌ Failed to clear data: ${error.message}`);
      } else {
        alert('❌ Failed to clear data due to an unknown error.');
      }
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    // Create new session if this is the first user message
    if (messages.length === 1 && !currentSessionId) {
      createNewSession(inputValue);
    }

    const userMessage: Message = {
      id: Date.now(),
      message: inputValue,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue
        })
      });

      const data = await response.json();
      
      if (data.success) {
        const aiResponse: Message = {
          id: Date.now() + 1,
          message: data.response,
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        message: "I'm sorry, I'm having trouble connecting to the medical AI system. Please try again later.",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleImageUpload = async (file: File) => {
    setIsLoading(true);

    // Create new session if this is the first interaction
    if (messages.length === 1 && !currentSessionId) {
      createNewSession(`📸 Uploaded image: ${file.name}`);
    }

    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64String = reader.result as string;

        const response = await fetch(`${API_URL}/api/analyze-image`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ image: base64String }),
        });

        const data = await response.json();

        if (data.success) {
          const newMessage: Message = {
            id: Date.now(),
            message: `📸 Uploaded image: ${file.name}`,
            isUser: true,
            timestamp: new Date(),
          };

          const aiResponse: Message = {
            id: Date.now() + 1,
            message: data.response,
            isUser: false,
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, newMessage, aiResponse]);
        } else {
          const errorMessage: Message = {
            id: Date.now(),
            message: `❌ Image analysis failed: ${data.error}`,
            isUser: false,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMessage]);
        }
      };

      reader.readAsDataURL(file);
    } catch (error) {
      console.error("Image upload error:", error);
      const errorMessage: Message = {
        id: Date.now(),
        message: "❌ Failed to analyze image. Please try again.",
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleQuickPrompt = async (prompt: string) => {
    // Create new session if this is the first interaction
    if (messages.length === 1 && !currentSessionId) {
      createNewSession(prompt);
    }

    const userMessage: Message = {
      id: Date.now(),
      message: prompt,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: prompt
        })
      });

      const data = await response.json();
      
      if (data.success) {
        const aiResponse: Message = {
          id: Date.now() + 1,
          message: data.response,
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        message: "I'm sorry, I'm having trouble connecting to the medical AI system. Please try again later.",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const medicalChatHistory = [
    "Understanding IDC Diagnosis",
    "Treatment Options Overview", 
    "Hormone Receptor Status",
    "Chemotherapy Side Effects",
    "Radiation Therapy Questions",
    "Surgical Options Discussion",
    "Staging and Prognosis",
    "Support Resources"
  ];

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      background: '#1a1a2e',
      color: 'white',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Sidebar */}
      <div style={{
        width: sidebarOpen ? '280px' : '0',
        background: '#16213e',
        borderRight: '1px solid #0f3460',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.3s ease',
        overflow: 'hidden'
      }}>
        {/* Sidebar Header */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #0f3460'
        }}>
          <button 
            onClick={handleNewConsultation}
            style={{
              width: '100%',
              padding: '14px',
              background: 'linear-gradient(135deg, #e53e3e, #c53030)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontWeight: '600',
              fontSize: '14px',
              marginBottom: '12px'
            }}>
            <span>🩺</span>
            New Consultation
          </button>

          {/* Clear All Data Button */}
          <button 
            onClick={handleClearAllData}
            style={{
              width: '100%',
              padding: '12px',
              background: 'transparent',
              border: '1px solid #e53e3e',
              borderRadius: '8px',
              color: '#e53e3e',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontWeight: '600',
              fontSize: '13px',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#e53e3e';
              e.currentTarget.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.color = '#e53e3e';
            }}
          >
            <span>🗑️</span>
            Clear All Data
          </button>

          {/* Privacy Notice - Collapsible */}
          <div style={{ 
            marginTop: '12px', 
            background: '#0f1419',
            borderRadius: '6px',
            overflow: 'hidden',
            border: '1px solid #0f3460'
          }}>
            <button
              onClick={() => setPrivacyExpanded(!privacyExpanded)}
              style={{
                width: '100%',
                padding: '12px',
                background: 'transparent',
                border: 'none',
                color: '#a0aec0',
                fontSize: '11px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                textAlign: 'left'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '14px' }}>🔒</span>
                <span>Your Privacy Matters</span>
              </div>
              <span style={{ fontSize: '14px' }}>{privacyExpanded ? '−' : '+'}</span>
            </button>
            
            {privacyExpanded && (
              <div style={{ 
                padding: '0 12px 12px 12px',
                fontSize: '11px', 
                color: '#718096',
                lineHeight: '1.5'
              }}>
                Feel free to share your medical information. You have full control - delete all your data anytime using the button above.
              </div>
            )}
          </div>
        </div>

        {/* Medical Categories */}
        <div style={{ padding: '16px', borderBottom: '1px solid #0f3460' }}>
          <div style={{ marginBottom: '12px', fontSize: '14px', color: '#a0aec0', fontWeight: '600' }}>
            📋 Medical Resources
          </div>
          {[
            { title: '🔬 Breast Cancer Guidelines', file: '8577.00.pdf' },
            { title: '💊 Treatment Protocols', file: '8579.00.pdf' },
            { title: '🤝 Patient Care Standards', file: '8581.00.pdf' }
          ].map((resource, index) => (
            <a
              key={index}
              href={`/texts/${resource.file}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                color: '#cbd5e0',
                cursor: 'pointer',
                padding: '4px 0',
                textDecoration: 'none',
                transition: 'color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#e53e3e';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#cbd5e0';
              }}
            >
              {resource.title}
            </a>
          ))}
          
          {/* Copyright Notice - Collapsible */}
          <div style={{ 
            marginTop: '16px', 
            background: '#0f1419',
            borderRadius: '6px',
            overflow: 'hidden'
          }}>
            <button
              onClick={() => setCopyrightExpanded(!copyrightExpanded)}
              style={{
                width: '100%',
                padding: '12px',
                background: 'transparent',
                border: 'none',
                color: '#a0aec0',
                fontSize: '11px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                textAlign: 'left'
              }}
            >
              <span>© Copyright Notice</span>
              <span style={{ fontSize: '14px' }}>{copyrightExpanded ? '−' : '+'}</span>
            </button>
            
            {copyrightExpanded && (
              <div style={{ 
                padding: '0 12px 12px 12px',
                fontSize: '11px', 
                color: '#718096',
                lineHeight: '1.5'
              }}>
                <div style={{ marginBottom: '6px' }}>
                  Copyright "Invasive Breast Cancer (IDC/ILC)" American Cancer Society, Inc. Reprinted with permission from www.cancer.org.
                </div>
                <div style={{ marginBottom: '6px' }}>
                  Copyright "Breast Cancer Early Detection and Diagnosis" American Cancer Society, Inc. Reprinted with permission from www.cancer.org.
                </div>
                <div>
                  Copyright "Treating Breast Cancer" American Cancer Society, Inc. Reprinted with permission from www.cancer.org.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Chat History - Show actual sessions */}
        {chatSessions.length > 0 && (
          <div style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
            <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '12px', fontWeight: '600' }}>RECENT CONSULTATIONS</div>
            {chatSessions.map((session, index) => (
              <div 
                key={session.id} 
                onClick={() => {
                  setCurrentSessionId(session.id);
                  // You can load the session messages here if you want to switch between sessions
                }}
                style={{
                  padding: '10px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  marginBottom: '4px',
                  color: '#cbd5e0',
                  background: session.id === currentSessionId ? '#0f3460' : 'transparent',
                }}
                onMouseEnter={(e) => {
                  if (session.id !== currentSessionId) {
                    e.currentTarget.style.background = '#0f3460';
                  }
                }}
                onMouseLeave={(e) => {
                  if (session.id !== currentSessionId) {
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                {session.title}
              </div>
            ))}
          </div>
        )}

        {/* Spacer to push patient info to bottom */}
        {chatSessions.length === 0 && <div style={{ flex: 1 }} />}

        {/* User Profile - Fixed at bottom */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid #0f3460',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginTop: 'auto'
        }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #e53e3e, #c53030)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            🩺
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', fontWeight: '600' }}>Patient Portal</div>
            <div style={{ fontSize: '12px', color: '#a0aec0' }}>AI Connected ✅</div>
          </div>
          <button style={{
            padding: '6px 12px',
            background: 'transparent',
            border: '1px solid #0f3460',
            borderRadius: '6px',
            color: '#cbd5e0',
            fontSize: '12px',
            cursor: 'pointer'
          }}>
            Settings
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        background: '#1a1a2e'
      }}>
        {/* Top Bar */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid #0f3460',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#16213e'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '18px'
              }}
            >
              ☰
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #e53e3e, #c53030)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '16px'
              }}>
                🩺
              </div>
              <h1 style={{ 
                fontSize: '20px', 
                fontWeight: '700',
                margin: 0,
                background: 'linear-gradient(135deg, #e53e3e, #ff6b6b)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                INVADUCTAR GPT
              </h1>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              padding: '6px 12px',
              background: '#0f3460',
              borderRadius: '16px',
              fontSize: '12px',
              color: '#a0aec0'
            }}>
              🤖 DeepSeek + Vision AI Active
            </div>
            <button style={{
              padding: '8px 16px',
              background: 'linear-gradient(135deg, #e53e3e, #c53030)',
              border: 'none',
              borderRadius: '20px',
              color: 'white',
              fontSize: '13px',
              cursor: 'pointer',
              fontWeight: '600'
            }}>
              💝 Donate
            </button>
          </div>
        </div>

        {/* Chat Messages Area */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {messages.length === 1 ? (
            // Welcome Screen
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center'
            }}>
              <div style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #e53e3e, #c53030)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '32px',
                marginBottom: '24px'
              }}>
                🩺
              </div>
              <h1 style={{
                fontSize: '36px',
                fontWeight: '300',
                marginBottom: '16px',
                color: 'white'
              }}>
                How can I help you today?
              </h1>
              <p style={{
                fontSize: '16px',
                color: '#a0aec0',
                maxWidth: '600px',
                lineHeight: '1.6',
                marginBottom: '32px'
              }}>
                I'm powered by advanced AI models including image analysis and DeepSeek for 
                evidence-based breast cancer information and support.
              </p>
              
              {/* Image Upload Component */}
              <div style={{ marginBottom: '32px' }}>
                <ImageUpload onImageUpload={handleImageUpload} />
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '16px',
                maxWidth: '800px',
                width: '100%'
              }}>
                {[
                  { icon: '🔬', title: 'Understanding IDC', desc: 'Learn about invasive ductal carcinoma', prompt: 'Can you explain what invasive ductal carcinoma (IDC) is and how it differs from other types of breast cancer?' },
                  { icon: '💊', title: 'Treatment Options', desc: 'Explore available treatments', prompt: 'What are the main treatment options available for invasive ductal carcinoma?' },
                  { icon: '🤝', title: 'Support Resources', desc: 'Find emotional and practical support', prompt: 'What support resources are available for patients diagnosed with invasive ductal carcinoma?' },
                  { icon: '📊', title: 'Prognosis Info', desc: 'Understand staging and outcomes', prompt: 'Can you explain the staging system for invasive ductal carcinoma and what it means for prognosis?' }
                ].map((item, index) => (
                  <div 
                    key={index} 
                    onClick={() => handleQuickPrompt(item.prompt)}
                    style={{
                      padding: '20px',
                      background: '#16213e',
                      borderRadius: '12px',
                      border: '1px solid #0f3460',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#0f3460';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(229, 62, 62, 0.2)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#16213e';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <div style={{ fontSize: '24px', marginBottom: '8px' }}>{item.icon}</div>
                    <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px', color: 'white' }}>{item.title}</div>
                    <div style={{ fontSize: '14px', color: '#a0aec0' }}>{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            // Chat Messages
            <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg.message}
                  isUser={msg.isUser}
                  timestamp={msg.timestamp}
                />
              ))}
              {isTyping && <TypingIndicator />}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div style={{ 
          padding: '20px',
          borderTop: messages.length > 1 ? '1px solid #0f3460' : 'none',
          background: '#16213e'
        }}>
          <div style={{ 
            maxWidth: '800px', 
            margin: '0 auto',
            position: 'relative'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'flex-end',
              background: '#1a1a2e',
              borderRadius: '24px',
              padding: '12px 16px',
              gap: '12px',
              border: '1px solid #0f3460'
            }}>
              <label style={{
                background: 'transparent',
                border: 'none',
                color: '#a0aec0',
                cursor: 'pointer',
                fontSize: '18px'
              }}>
                📎
                <input 
                  type="file" 
                  accept="image/*" 
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleImageUpload(file);
                  }}
                />
              </label>
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about breast cancer, treatments, or upload a medical image..."
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  fontSize: '16px',
                  resize: 'none',
                  outline: 'none',
                  minHeight: '24px',
                  maxHeight: '120px',
                  fontFamily: 'inherit'
                }}
                rows={1}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim()}
                style={{
                  background: inputValue.trim() ? 'linear-gradient(135deg, #e53e3e, #c53030)' : '#0f3460',
                  border: 'none',
                  borderRadius: '50%',
                  width: '36px',
                  height: '36px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: inputValue.trim() ? 'pointer' : 'not-allowed',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
              >
                ↑
              </button>
            </div>
            <div style={{
              textAlign: 'center',
              marginTop: '12px',
              fontSize: '12px',
              color: '#a0aec0'
            }}>
              INVADUCTAR GPT with DeepSeek AI • Always consult healthcare professionals for medical advice.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
