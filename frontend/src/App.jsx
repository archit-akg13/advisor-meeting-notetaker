import { useState, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function StatusBadge({ status }) {
  const colors = {
    GREEN: { bg: '#E8F5E9', text: '#2E7D32', label: 'PASS' },
    YELLOW: { bg: '#FFF3E0', text: '#E65100', label: 'REVIEW' },
    RED: { bg: '#FFEBEE', text: '#C62828', label: 'FLAG' },
  };
  const c = colors[status] || colors.GREEN;
  return (
    <span style={{
      background: c.bg, color: c.text, padding: '2px 10px',
      borderRadius: 4, fontWeight: 700, fontSize: 12, letterSpacing: 0.5
    }}>{c.label}</span>
  );
}

function CompliancePanel({ compliance }) {
  if (!compliance) return null;
  return (
    <div style={{ background: '#FAFAFA', borderRadius: 8, padding: 20, marginTop: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <h3 style={{ margin: 0, fontSize: 16 }}>Compliance Check</h3>
        <StatusBadge status={compliance.overall} />
      </div>
      {compliance.rules.map(rule => (
        <div key={rule.id} style={{
          background: '#fff', borderRadius: 6, padding: 14, marginBottom: 10,
          borderLeft: `4px solid ${rule.color}`
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: 13 }}>{rule.name}</strong>
            <StatusBadge status={rule.status} />
          </div>
          <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 13, color: '#555' }}>
            {rule.flags.map((flag, i) => <li key={i} style={{ marginBottom: 4 }}>{flag}</li>)}
          </ul>
          {rule.recommendation && rule.status !== 'GREEN' && (
            <p style={{ fontSize: 12, color: rule.color, margin: '6px 0 0', fontStyle: 'italic' }}>
              {rule.recommendation}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function CRMNote({ note }) {
  if (!note) return null;
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(note);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0, fontSize: 16 }}>CRM-Ready Note</h3>
        <button onClick={copy} style={{
          background: copied ? '#4CAF50' : '#1B2A4A', color: '#fff', border: 'none',
          padding: '6px 16px', borderRadius: 4, cursor: 'pointer', fontSize: 13
        }}>{copied ? 'Copied!' : 'Copy to Clipboard'}</button>
      </div>
      <pre style={{
        background: '#1B2A4A', color: '#E0E0E0', padding: 20, borderRadius: 8,
        fontSize: 12, lineHeight: 1.6, overflow: 'auto', maxHeight: 500, whiteSpace: 'pre-wrap'
      }}>{note}</pre>
    </div>
  );
}

function MeetingData({ data }) {
  if (!data) return null;
  return (
    <div style={{ background: '#F0F4FF', borderRadius: 8, padding: 20, marginTop: 16 }}>
      <h3 style={{ margin: '0 0 12px', fontSize: 16 }}>Extracted Meeting Data</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div><strong>Client:</strong> {data.client_name}</div>
        <div><strong>Advisor:</strong> {data.advisor_name}</div>
        <div><strong>Type:</strong> {(data.meeting_type || '').replace(/_/g, ' ')}</div>
        <div><strong>Date:</strong> {data.meeting_date || 'Not specified'}</div>
      </div>
      {data.discussion_topics?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <strong>Topics:</strong>
          <ul style={{ margin: '4px 0', paddingLeft: 18 }}>
            {data.discussion_topics.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        </div>
      )}
      {data.action_items?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <strong>Action Items:</strong>
          <ul style={{ margin: '4px 0', paddingLeft: 18 }}>
            {data.action_items.map((a, i) => (
              <li key={i}>[{(a.owner || 'advisor').toUpperCase()}] {a.task}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/process`, { method: 'POST', body: formData });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Processing failed');
      }
      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '40px 20px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <h1 style={{ fontSize: 28, color: '#1B2A4A', margin: '0 0 8px' }}>
          Advisor Meeting AI Notetaker
        </h1>
        <p style={{ color: '#666', fontSize: 15, margin: 0 }}>
          Upload a meeting recording. Get compliant, CRM-ready notes in 30 seconds.
        </p>
      </div>

      {/* Upload area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? '#FF6B35' : '#ccc'}`,
          borderRadius: 12, padding: 40, textAlign: 'center',
          background: dragActive ? '#FFF3E0' : '#FAFAFA',
          transition: 'all 0.2s', cursor: 'pointer'
        }}
        onClick={() => document.getElementById('fileInput').click()}
      >
        <input
          id="fileInput" type="file" hidden
          accept=".mp3,.wav,.m4a,.webm,.mp4,.ogg,.flac"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <div style={{ fontSize: 40, marginBottom: 12 }}>
          {file ? 'â' : 'ð¤'}
        </div>
        <p style={{ fontSize: 15, color: '#333', margin: '0 0 8px' }}>
          {file ? file.name : 'Drop meeting recording here or click to browse'}
        </p>
        <p style={{ fontSize: 12, color: '#999', margin: 0 }}>
          Supports MP3, WAV, M4A, WebM, MP4, OGG, FLAC (max 100MB)
        </p>
      </div>

      {file && !loading && !result && (
        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <button onClick={handleSubmit} style={{
            background: '#FF6B35', color: '#fff', border: 'none', padding: '12px 32px',
            borderRadius: 6, fontSize: 15, fontWeight: 600, cursor: 'pointer'
          }}>Process Meeting Recording</button>
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', marginTop: 30, color: '#1B2A4A' }}>
          <div style={{ fontSize: 24, marginBottom: 12, animation: 'spin 1s linear infinite' }}>
            {'âï¸'}
          </div>
          <p style={{ fontSize: 14 }}>Processing... Transcribing audio, extracting data, running compliance checks</p>
        </div>
      )}

      {error && (
        <div style={{ background: '#FFEBEE', color: '#C62828', padding: 16, borderRadius: 8, marginTop: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 20 }}>
          <div style={{
            background: '#E8F5E9', padding: 12, borderRadius: 8, textAlign: 'center',
            fontSize: 14, color: '#2E7D32', marginBottom: 16
          }}>
            Processed in {result.processing_time_seconds}s | Duration: {Math.round(result.transcript?.duration || 0)}s
          </div>

          {/* Transcript */}
          <details style={{ marginTop: 16 }}>
            <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: 16, color: '#1B2A4A' }}>
              Full Transcript ({result.transcript?.segments?.length || 0} segments)
            </summary>
            <div style={{
              background: '#f5f5f5', padding: 16, borderRadius: 8, marginTop: 8,
              maxHeight: 300, overflow: 'auto', fontSize: 13, lineHeight: 1.8
            }}>
              {result.transcript?.segments?.map((seg, i) => (
                <p key={i} style={{ margin: '4px 0' }}>
                  <span style={{ color: '#999', fontSize: 11 }}>[{seg.start}s]</span> {seg.text}
                </p>
              ))}
            </div>
          </details>

          <MeetingData data={result.meeting_data} />
          <CompliancePanel compliance={result.compliance} />
          <CRMNote note={result.crm_note} />
        </div>
      )}

      <footer style={{ textAlign: 'center', marginTop: 40, padding: 20, color: '#999', fontSize: 12 }}>
        Built by <a href="https://architmittal.com" style={{ color: '#FF6B35' }}>Archit Mittal</a> |
        AI & Automation Consultant for Financial Services
      </footer>
    </div>
  );
}
