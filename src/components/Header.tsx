interface HeaderProps {}

export default function Header({}: HeaderProps) {
  return (
    <header style={{
      background: 'white',
      borderBottom: '1px solid #e5e7eb',
      padding: '1rem 2rem',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <h1 style={{
          fontSize: '1.5rem',
          fontWeight: 'bold',
          color: '#1f2937',
          margin: 0
        }}>
          📄 Document AI Assistant
        </h1>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <span style={{
            fontSize: '0.875rem',
            color: '#6b7280'
          }}>
            Ready to analyze your documents
          </span>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981'
          }} />
        </div>
      </div>
    </header>
  );
}