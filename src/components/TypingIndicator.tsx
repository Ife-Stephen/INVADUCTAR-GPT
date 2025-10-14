interface TypingIndicatorProps {}

export default function TypingIndicator({}: TypingIndicatorProps) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'flex-start',
      marginBottom: '32px',
      gap: '16px'
    }}>
      {/* AI Avatar */}
      <div style={{
        width: '40px',
        height: '40px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #e53e3e, #c53030)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '16px',
        fontWeight: 'bold',
        color: 'white',
        flexShrink: 0,
        border: '2px solid #0f3460'
      }}>
        🩺
      </div>
      
      {/* Typing Animation */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#a0aec0',
          fontSize: '16px'
        }}>
          <div style={{
            display: 'flex',
            gap: '4px',
            alignItems: 'center'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#e53e3e',
              animation: 'pulse 1.5s ease-in-out infinite'
            }} />
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#e53e3e',
              animation: 'pulse 1.5s ease-in-out infinite 0.2s'
            }} />
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#e53e3e',
              animation: 'pulse 1.5s ease-in-out infinite 0.4s'
            }} />
          </div>
          <span style={{ marginLeft: '8px' }}>
            INVADUCTAR GPT is analyzing...
          </span>
        </div>
        <div style={{ 
          marginTop: '8px',
          fontSize: '12px', 
          color: '#a0aec0'
        }}>
          Providing evidence-based breast cancer information
        </div>
      </div>
    </div>
  );
}