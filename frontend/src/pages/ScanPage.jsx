import { useState } from 'react';
import { scanContract } from '../services/api';
import { useNavigate } from 'react-router-dom';

function ScanPage() {
  const [code, setCode] = useState('');
  const [fileName, setFileName] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (event) => {
        setCode(event.target.result);
      };
      reader.onerror = () => alert('File read error');
      reader.readAsText(file);
    }
  };

  const handleScan = async () => {
    if (!code.trim()) {
      alert('Please paste code or upload a .sol file');
      return;
    }

    setLoading(true);
    try {
      const result = await scanContract(code);
      navigate('/results', { state: { result } });
    } catch (error) {
      alert('Scan failed: ' + (error.detail || error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '40px', maxWidth: '900px', margin: '0 auto', fontFamily: 'Arial' }}>
      <h1>BlockScope - Smart Contract Vulnerability Scanner</h1>
      <p>Paste Solidity code or upload a .sol file to scan for security issues.</p>

      <div style={{ marginBottom: '20px' }}>
        <input type="file" accept=".sol" onChange={handleFileUpload} />
        {fileName && <p>Uploaded: <strong>{fileName}</strong></p>}
      </div>

      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="// Paste your Solidity contract code here..."
        rows="20"
        style={{ width: '100%', padding: '12px', fontFamily: 'monospace', fontSize: '14px' }}
      />

      <button
        onClick={handleScan}
        disabled={loading}
        style={{
          marginTop: '20px',
          padding: '14px 30px',
          fontSize: '18px',
          background: loading ? '#999' : '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Scanning... (please wait)' : 'Scan Contract'}
      </button>

      {loading && <p style={{ marginTop: '20px', fontSize: '18px' }}>🔄 Analyzing with Semgrep...</p>}
    </div>
  );
}

export default ScanPage;