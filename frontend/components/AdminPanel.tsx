'use client';
import React from 'react';
import { apiIngest, apiMetrics } from '@/lib/api';

export default function AdminPanel() {
  const [metrics, setMetrics] = React.useState<any>(null);
  const [busy, setBusy] = React.useState(false);

  const refresh = async () => {
    const m = await apiMetrics();
    setMetrics(m);
  };

  const ingest = async () => {
    setBusy(true);
    try { await apiIngest(); await refresh(); } 
    finally { setBusy(false); }
  };

  React.useEffect(() => { refresh(); }, []);

  return (
    <div style={{ padding: '20px', background: '#f8f9fa', borderRadius: '12px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: metrics ? '16px' : '0' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: '600', color: '#444', textTransform: 'uppercase', letterSpacing: '0.05em' }}>System Control</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={ingest} disabled={busy} style={{ padding: '6px 14px', borderRadius: '6px', border: 'none', background: '#000', color: '#fff', fontSize: '0.85rem', cursor: 'pointer', opacity: busy ? 0.6 : 1 }}>
            {busy ? 'Indexing...' : 'Rebuild Index'}
          </button>
          <button onClick={refresh} style={{ padding: '6px 14px', borderRadius: '6px', border: '1px solid #ddd', background: '#fff', fontSize: '0.85rem', cursor: 'pointer' }}>Refresh</button>
        </div>
      </div>
      
      {metrics && (
        <details style={{ fontSize: '0.8rem', color: '#666' }}>
          <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>View system metrics</summary>
          <pre style={{ background: '#fff', padding: '12px', borderRadius: '6px', overflow: 'auto', border: '1px solid #eee' }}>
            {JSON.stringify(metrics, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}