import { useState } from 'react';

import { useAuditSocket } from '../hooks/useAuditSocket';

const defaultApiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [target, setTarget] = useState('');
  const [targetType, setTargetType] = useState('email');
  const [consent, setConsent] = useState(false);
  const [scanId, setScanId] = useState('');
  const [apiError, setApiError] = useState('');

  const { status, logs, results, error } = useAuditSocket(scanId);

  const submitScan = async (event) => {
    event.preventDefault();
    setApiError('');

    try {
      const response = await fetch(`${defaultApiBase}/api/v1/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, target_type: targetType, user_consent: consent }),
      });

      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || 'Scan request failed');
      }

      setScanId(body.scan_id);
    } catch (scanError) {
      setApiError(scanError.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <h1 className="text-2xl font-semibold">Digital Footprint & Cybersecurity Audit</h1>

        <div className="grid gap-6 md:grid-cols-2">
          <form onSubmit={submitScan} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-4">
            <label className="block text-sm">Target Type</label>
            <select
              value={targetType}
              onChange={(event) => setTargetType(event.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 p-2"
            >
              <option value="email">Email</option>
              <option value="phone">Phone</option>
            </select>

            <label className="block text-sm">Target</label>
            <input
              value={target}
              onChange={(event) => setTarget(event.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 p-2"
              placeholder={targetType === 'email' ? 'user@example.com' : '+1234567890'}
              required
            />

            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                checked={consent}
                onChange={(event) => setConsent(event.target.checked)}
                className="mt-1"
                required
              />
              <span>I confirm I have explicit authorization and legal consent for this scan.</span>
            </label>

            <button
              type="submit"
              disabled={!consent || status === 'processing'}
              className="w-full rounded bg-cyan-600 px-4 py-2 font-medium disabled:opacity-50"
            >
              {status === 'processing' ? 'Running scan…' : 'Start scan'}
            </button>

            {apiError ? <p className="text-sm text-red-400">{apiError}</p> : null}
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
          </form>

          <section className="rounded-xl border border-slate-800 bg-black p-4">
            <h2 className="mb-2 text-sm uppercase tracking-widest text-slate-400">Live Feed</h2>
            <div className="h-56 overflow-y-auto rounded border border-slate-800 bg-slate-950 p-3 font-mono text-xs">
              {logs.length === 0 ? <p className="text-slate-600">Waiting for scan output…</p> : null}
              {logs.map((log) => (
                <p key={log} className="text-emerald-400">
                  {log}
                </p>
              ))}
            </div>

            {results ? (
              <pre className="mt-3 overflow-x-auto rounded border border-slate-800 bg-slate-950 p-3 text-xs text-slate-200">
                {JSON.stringify(results, null, 2)}
              </pre>
            ) : null}
          </section>
        </div>
      </div>
    </div>
  );
}
