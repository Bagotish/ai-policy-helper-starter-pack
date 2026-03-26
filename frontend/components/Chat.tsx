'use client';
import React, { useRef, useEffect } from 'react'; 
import { apiAsk } from '@/lib/api';

type Message = { role: 'user' | 'assistant', content: string, citations?: {title:string, section?:string}[], chunks?: {title:string, section?:string, text:string}[] };

export default function Chat() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [q, setQ] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async () => {
    if (!q.trim()) return;
    const my = { role: 'user' as const, content: q };
    setMessages(m => [...m, my]);
    setLoading(true);
    setQ('');
    try {
      const res = await apiAsk(q);
      const ai: Message = { role: 'assistant', content: res.answer, citations: res.citations, chunks: res.chunks };
      setMessages(m => [...m, ai]);
    } catch (e:any) {
      setMessages(m => [...m, { role: 'assistant', content: 'Error: ' + e.message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '600px', border: '1px solid #eee', borderRadius: '16px', overflow: 'hidden', background: '#fff', boxShadow: '0 4px 24px rgba(0,0,0,0.04)' }}>
      {/* Messages Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#aaa', marginTop: '100px' }}>Ask a question to start the conversation...</div>
        )}
        
        {messages.map((m, i) => (
          <div key={i} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
            <div style={{ 
              padding: '12px 16px', 
              borderRadius: '12px', 
              fontSize: '0.95rem',
              lineHeight: '1.5',
              background: m.role === 'user' ? '#000' : '#f1f1f1',
              color: m.role === 'user' ? '#fff' : '#000'
            }}>
              {m.content}
            </div>
            
            {m.citations && m.citations.length > 0 && (
              <div style={{ marginTop: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {m.citations.map((c, idx) => (
                  <span key={idx} style={{ fontSize: '10px', padding: '2px 8px', background: '#eee', borderRadius: '4px', color: '#666' }}>
                    {c.title}
                  </span>
                ))}
              </div>
            )}
            
            {m.chunks && m.chunks.length > 0 && (
              <details style={{ marginTop: '8px' }}>
                <summary style={{ fontSize: '11px', color: '#999', cursor: 'pointer' }}>Sources</summary>
                <div style={{ marginTop: '8px', borderLeft: '2px solid #eee', paddingLeft: '12px', fontSize: '0.85rem', color: '#555' }}>
                  {m.chunks.map((c, idx) => (
                    <div key={idx} style={{ marginBottom: '8px' }}>
                      <strong>{c.section}</strong>: {c.text.substring(0, 150)}...
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        ))}
        {loading && <div style={{ fontSize: '0.85rem', color: '#999', alignSelf: 'flex-start' }}>AI is typing...</div>}
        <div ref={scrollRef} />
      </div>

      {/* Input Area */}
      <div style={{ padding: '20px', borderTop: '1px solid #eee', display: 'flex', gap: '12px', background: '#fff' }}>
        <input 
          placeholder="Type your question..." 
          value={q} 
          onChange={e => setQ(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && send()}
          style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid #eee', fontSize: '0.95rem', outline: 'none' }}
        />
        <button onClick={send} disabled={loading} style={{ padding: '0 20px', borderRadius: '8px', background: '#000', color: '#fff', border: 'none', fontWeight: '600', cursor: 'pointer' }}>
          Send
        </button>
      </div>
    </div>
  );
}