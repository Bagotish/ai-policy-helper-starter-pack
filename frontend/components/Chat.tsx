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
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]); 

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
    <div className="card">
      <h2>Chat</h2>
      <div style={{maxHeight: 400, overflowY:'auto', padding: 12, border:'1px solid #eee', borderRadius: 8, marginBottom: 12}}>
        {messages.map((m, i) => (
          <div key={i} style={{margin: '12px 0', borderBottom: '1px solid #fafafa', paddingBottom: 8}}>
            <div style={{fontSize:11, fontWeight: 700, color: m.role === 'user' ? '#007bff' : '#28a745', textTransform: 'uppercase'}}>
              {m.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div style={{marginTop: 4, lineHeight: 1.5}}>{m.content}</div>
            
            {m.citations && m.citations.length > 0 && (
              <div style={{marginTop:6, display: 'flex', gap: 4, flexWrap: 'wrap'}}>
                {m.citations.map((c, idx) => (
                  <span key={idx} className="badge" style={{fontSize: 10}} title={c.section || ''}>{c.title}</span>
                ))}
              </div>
            )}
            
            {m.chunks && m.chunks.length > 0 && (
              <details style={{marginTop:8, fontSize: 13}}>
                <summary style={{cursor: 'pointer', color: '#666'}}>View supporting chunks</summary>
                {m.chunks.map((c, idx) => (
                  <div key={idx} className="card" style={{padding: 8, background: '#f9f9f9', marginTop: 4}}>
                    <div style={{fontWeight:600, fontSize: 12}}>{c.title}{c.section ? ' — ' + c.section : ''}</div>
                    <div style={{whiteSpace:'pre-wrap', fontSize: 11, color: '#444'}}>{c.text}</div>
                  </div>
                ))}
              </details>
            )}
          </div>
        ))}
        
        <div ref={scrollRef} /> 
      </div>

      <div style={{display:'flex', gap:8}}>
        <input 
          placeholder="Ask about policy or products..." 
          value={q} 
          onChange={e=>setQ(e.target.value)} 
          style={{flex:1, padding:12, borderRadius:8, border:'1px solid #ddd'}} 
          onKeyDown={(e)=>{ if(e.key==='Enter') send(); }}
        />
        <button onClick={send} disabled={loading} style={{padding:'0px 20px', borderRadius:8, border:'none', background:'#111', color:'#fff', fontWeight: 600, cursor: 'pointer'}}>
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}