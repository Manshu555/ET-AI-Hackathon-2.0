"use client";
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function RfiChatPage() {
  const [messages, setMessages] = useState<{role: string, content: string}[]>([
    { role: 'ai', content: 'Hello! I am your EPC-Intel assistant. Ask me anything about the project specifications or submittals.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    const currentInput = input;
    setInput('');
    setLoading(true);
    
    try {
      // session_id hardcoded for demonstration
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/rfi/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: "demo-session-123", message: currentInput })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'ai', content: data.reply || 'Error: No response' }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'ai', content: 'Network error communicating with the API.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">RFI Chat Assistant</h1>
      
      <div className="flex-1 glass rounded-t-2xl p-6 overflow-y-auto space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-primary text-white rounded-tr-none' : 'bg-secondary/80 border border-white/5 rounded-tl-none'}`}>
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] p-4 rounded-2xl bg-secondary/80 border border-white/5 rounded-tl-none">
              <div className="flex space-x-2 items-center h-5">
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>
      
      <div className="glass rounded-b-2xl p-4 border-t border-white/5">
        <form onSubmit={handleSend} className="flex gap-2">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask a question about the project..." 
            className="flex-1 bg-secondary/50 border border-white/10 rounded-lg px-4 py-3 focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
          />
          <button type="submit" disabled={loading || !input.trim()} className="bg-primary hover:bg-primary-hover disabled:bg-gray-600 text-white px-6 py-3 rounded-lg font-medium transition-colors">
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
