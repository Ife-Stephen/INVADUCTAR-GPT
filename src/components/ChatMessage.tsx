interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp: Date;
}

export default function ChatMessage({ 
  message, 
  isUser, 
  timestamp 
}: ChatMessageProps) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'flex-start',
      marginBottom: '32px',
      gap: '16px'
    }}>
      {/* Avatar */}
      <div style={{
        width: '40px',
        height: '40px',
        borderRadius: '50%',
        background: isUser 
          ? 'linear-gradient(135deg, #4299e1, #3182ce)' 
          : 'linear-gradient(135deg, #e53e3e, #c53030)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '16px',
        fontWeight: 'bold',
        color: 'white',
        flexShrink: 0,
        border: '2px solid #0f3460'
      }}>
        {isUser ? '👤' : '🩺'}
      </div>
      
      {/* Message Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          background: 'transparent',
          color: 'white',
          fontSize: '16px',
          lineHeight: '1.6',
          wordWrap: 'break-word'
        }}>
          {message}
        </div>
        <div style={{ 
          marginTop: '8px',
          fontSize: '12px', 
          color: '#a0aec0',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span>{timestamp.toLocaleTimeString()}</span>
          {!isUser && (
            <>
              <span>•</span>
              <span>Medical AI Assistant</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}