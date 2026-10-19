import React, { useEffect, useState } from 'react';
import { api, ScanEvent } from '../api';
import { Search, RefreshCw, Clock } from 'lucide-react';

export const ScansView: React.FC = () => {
  const [scans, setScans] = useState<ScanEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [resultFilter, setResultFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const loadScans = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getScans(resultFilter);
      setScans(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load scan history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScans();
  }, [resultFilter]);

  const filteredScans = scans.filter((s) => {
    const term = searchTerm.toLowerCase();
    const matchesProduct = (s.product_name || '').toLowerCase().includes(term);
    const matchesId = (s.product_id || '').toLowerCase().includes(term);
    const matchesReason = (s.risk_reason || '').toLowerCase().includes(term);
    const matchesLoc = (s.scan_location || '').toLowerCase().includes(term);
    return matchesProduct || matchesId || matchesReason || matchesLoc;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Scan Audit & Security History</h1>
          <p className="page-subtitle">
            Comprehensive audit log of all verification and registration scans recorded in Scan_History
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadScans}>
          <RefreshCw size={15} /> Refresh Logs
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        {/* Filters */}
        <div className="filter-bar">
          <div className="search-input-wrap">
            <Search className="search-icon" size={16} />
            <input
              type="text"
              placeholder="Search by product, location, or risk reason..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            className="select-filter"
            value={resultFilter}
            onChange={(e) => setResultFilter(e.target.value)}
          >
            <option value="ALL">All Results</option>
            <option value="VERIFIED">VERIFIED Only</option>
            <option value="SUSPICIOUS">SUSPICIOUS Only</option>
            <option value="INVALID">INVALID Only</option>
          </select>
        </div>

        {/* Scan Table */}
        {loading && scans.length === 0 ? (
          <div className="state-box">
            <div className="spinner"></div>
            <p>Fetching scan audit records...</p>
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="state-box">
            <Clock size={36} color="var(--text-muted)" />
            <p>No scan history records match your filter.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Product</th>
                  <th>Scan Type</th>
                  <th>Location</th>
                  <th>Result</th>
                  <th>Security Explanation / Risk Notes</th>
                </tr>
              </thead>
              <tbody>
                {filteredScans.map((s) => (
                  <tr key={s.scan_id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {new Date(s.scanned_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{s.product_name || 'Unrecognized Item'}</div>
                      <div className="mono" style={{ color: '#818cf8', fontSize: '0.78rem' }}>
                        {s.product_id || 'None'}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: s.scan_type.includes('EXTERNAL') ? '#38bdf8' : '#a78bfa' }}>
                        {s.scan_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {s.scan_location || 'Not self-reported'}
                    </td>
                    <td>
                      <span className={`badge ${s.result}`}>{s.result}</span>
                    </td>
                    <td style={{ fontSize: '0.84rem', color: s.risk_reason ? '#fde68a' : 'var(--text-muted)', maxWidth: '300px' }}>
                      {s.risk_reason || 'Verified legitimate query without flags'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
