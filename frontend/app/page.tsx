import Chat from '@/components/Chat';
import AdminPanel from '@/components/AdminPanel';

export default function Page() {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '60px 20px', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <header style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '800', letterSpacing: '-0.02em', marginBottom: '8px' }}>
        AI Policy & Product Helper
               </h1>
        <p style={{ color: '#666', fontSize: '1.1rem' }}>
          Intelligent RAG assistant for corporate policies and documentation.
        </p>
      </header>

      <AdminPanel />
      
      <div style={{ margin: '40px 0' }}>
        <Chat />
      </div>

      <footer style={{ marginTop: '60px', padding: '20px', borderTop: '1px solid #eee', fontSize: '0.9rem', color: '#888' }}>
        <strong>Quick Start:</strong> Ingest the sample docs first, then ask about "Can a customer return a damaged blender after 20 days?" or "What’s the shipping SLA to East Malaysia for bulky items?".
      </footer>
    </div>
  );
}     
