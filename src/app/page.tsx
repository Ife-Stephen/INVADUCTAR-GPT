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

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, message: "Hello! I'm INVADUCTAR GPT, your specialized assistant for invasive ductal carcinoma information. I can help you understand breast cancer diagnosis, treatment options, and provide support. How can I assist you today?", isUser: false, timestamp: new Date() }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // Load conversation on mount
  useEffect(() => {
    loadConversation();
  }, []);

  const loadConversation = async () => {
    try {
      const response = await fetch('/api/conversation');
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

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

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
      const response = await fetch('/api/chat', {
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
    
    try {
      const formData = new FormData();
      formData.append('image', file);
      
      const response = await fetch('/api/image', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (data.success) {
        const newMessage = {
          id: messages.length + 1,
          message: `📸 Uploaded image: ${file.name}`,
          isUser: true,
          timestamp: new Date()
        };
        
        const aiResponse = {
          id: messages.length + 2,
          message: data.response,
          isUser: false,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, newMessage, aiResponse]);
      } else {
        const errorMessage = {
          id: messages.length + 1,
          message: `❌ Image analysis failed: ${data.error}`,
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Image upload error:', error);
      const errorMessage = {
        id: messages.length + 1,
        message: "❌ I'm sorry, I couldn't analyze the image. Please ensure it's a valid medical image and try again.",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
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
          <button style={{
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
            fontSize: '14px'
          }}>
            <span>🩺</span>
            New Consultation
          </button>
        </div>

        {/* Medical Categories */}
        <div style={{ padding: '16px', borderBottom: '1px solid #0f3460' }}>
          <div style={{ marginBottom: '12px', fontSize: '14px', color: '#a0aec0', fontWeight: '600' }}>
            📋 Medical Resources
          </div>
          <div style={{ marginBottom: '8px', fontSize: '14px', color: '#cbd5e0', cursor: 'pointer', padding: '4px 0' }}>
            🔬 Diagnostic Information
          </div>
          <div style={{ marginBottom: '8px', fontSize: '14px', color: '#cbd5e0', cursor: 'pointer', padding: '4px 0' }}>
            💊 Treatment Guidelines
          </div>
          <div style={{ fontSize: '14px', color: '#cbd5e0', cursor: 'pointer', padding: '4px 0' }}>
            🤝 Support Network
          </div>
        </div>

        {/* Specialized Tools */}
        <div style={{ padding: '16px', borderBottom: '1px solid #0f3460' }}>
          <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '8px', fontWeight: '600' }}>SPECIALIZED TOOLS</div>
          <div style={{ fontSize: '14px', color: '#cbd5e0', marginBottom: '6px', cursor: 'pointer', padding: '4px 0' }}>
            🎯 Risk Assessment
          </div>
          <div style={{ fontSize: '14px', color: '#cbd5e0', cursor: 'pointer', padding: '4px 0' }}>
            📊 Treatment Tracker
          </div>
        </div>

        {/* Chat History - Only show if there are multiple messages */}
        {messages.length > 1 && (
          <div style={{ flex: 1, padding: '16px' }}>
            <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '12px', fontWeight: '600' }}>RECENT CONSULTATIONS</div>
            {medicalChatHistory.slice(0, Math.min(messages.length - 1, 8)).map((chat, index) => (
              <div key={index} style={{
                padding: '10px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                marginBottom: '4px',
                color: '#cbd5e0',
                background: index === 0 ? '#0f3460' : 'transparent',
                ':hover': { background: '#0f3460' }
              }}>
                {chat}
              </div>
            ))}
          </div>
        )}

        {/* User Profile */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid #0f3460',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
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
              🏥 Connect with Oncologist
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
                  { icon: '🔬', title: 'Understanding IDC', desc: 'Learn about invasive ductal carcinoma' },
                  { icon: '💊', title: 'Treatment Options', desc: 'Explore available treatments' },
                  { icon: '🤝', title: 'Support Resources', desc: 'Find emotional and practical support' },
                  { icon: '📊', title: 'Prognosis Info', desc: 'Understand staging and outcomes' }
                ].map((item, index) => (
                  <div key={index} style={{
                    padding: '20px',
                    background: '#16213e',
                    borderRadius: '12px',
                    border: '1px solid #0f3460',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}>
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