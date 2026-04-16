import { useEffect, useState } from 'react';

const defaultWsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useAuditSocket(scanId) {
  const [status, setStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!scanId || scanId === 'cached') return undefined;

    const ws = new WebSocket(`${defaultWsBase}/ws/${scanId}`);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.status) setStatus(payload.status);
        if (payload.step) {
          setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${payload.step}`]);
        }
        if (payload.data) setResults(payload.data);
        if (payload.error) setError(payload.error);
      } catch {
        setError('Invalid WebSocket payload received');
      }
    };

    ws.onerror = () => setError('WebSocket connection failed');

    return () => {
      ws.close();
    };
  }, [scanId]);

  return { status, logs, results, error };
}
