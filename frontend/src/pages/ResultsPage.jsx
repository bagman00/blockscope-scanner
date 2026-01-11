import { useLocation, Link } from 'react-router-dom';

function ResultsPage() {
  const location = useLocation();
  const result = location.state?.result;

  const severityColor = {
    ERROR: '#dc3545',
    WARNING: '#fd7e14',
    INFO: '#17a2b8'
  };

  if (!result) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h1>No results</h1>
        <Link to="/">← Back to scan</Link>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', maxWidth: '900px', margin: '0 auto' }}>
      <h1>Scan Results</h1>
      <p><strong>Scan ID:</strong> {result.scan_id}</p>
      <p><strong>Risk Score:</strong> <span style={{ fontSize: '28px', color: result.score > 50 ? 'red' : result.score > 20 ? 'orange' : 'green' }}>{result.score}/100</span></p>

      <h2>Findings ({result.vulnerabilities.length})</h2>

      {result.vulnerabilities.length === 0 ? (
        <div style={{ padding: '40px', background: '#d4edda', borderRadius: '8px', textAlign: 'center' }}>
          <h3 style={{ color: '#155724' }}>🎉 No vulnerabilities found - Contract is SAFE!</h3>
        </div>
      ) : (
        result.vulnerabilities.map((vuln, i) => (
          <div key={i} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px', margin: '20px 0', background: '#f8f9fa' }}>
            <h3 style={{ color: severityColor[vuln.severity] || '#666', margin: '0 0 10px 0' }}>
              <span style={{ background: severityColor[vuln.severity] || '#666', color: 'white', padding: '4px 10px', borderRadius: '4px', fontSize: '14px' }}>
                {vuln.severity}
              </span> {vuln.type}
            </h3>
            <p><strong>Description:</strong> {vuln.description}</p>
            {vuln.line && <p><strong>Line:</strong> {vuln.line}</p>}
          </div>
        ))
      )}

      <Link to="/" style={{ display: 'inline-block', marginTop: '30px', fontSize: '18px', color: '#007bff' }}>
        ← Scan Another Contract
      </Link>
    </div>
  );
}

export default ResultsPage;