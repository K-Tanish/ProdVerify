import React, { useEffect, useState } from 'react';
import { api, DashboardStats, ScanEvent } from '../api';
import { 
  Package, 
  ShieldCheck, 
  AlertTriangle, 
  QrCode, 
  CheckCircle, 
  Clock, 
  RefreshCw,
  ExternalLink
} from 'lucide-react';

interface DashboardViewProps {
  onNavigate: (tab: string) => void;
  onVerifyToken: (token: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentScans, setRecentScans] = useState<ScanEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, scansData] = await Promise.all([
        api.getStats(),
        api.getScans(),
      ]);
      setStats(statsData);
      setRecentScans(scansData.slice(0, 5));
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !stats) {
    return (
      <div className="state-box">
        <div className="spinner"></div>
        <p>Connecting to ProdVerify backend database...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Manufacturer Overview Dashboard</h1>
          <p className="page-subtitle">
            Real-time anti-counterfeit analytics and warranty activity derived from counterfeit.db
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadData} title="Refresh live statistics">
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Real-time Metric Cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Total Products</span>
            <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
              <Package size={18} />
            </div>
          </div>
          <div className="stat-val">{stats?.total_products ?? 0}</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Registered physical units</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">In-Stock</span>
            <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
              <CheckCircle size={18} />
            </div>
          </div>
          <div className="stat-val" style={{ color: '#34d399' }}>{stats?.in_stock_products ?? 0}</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Authorized in channel</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Sold Units</span>
            <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>
              <Package size={18} />
            </div>
          </div>
          <div className="stat-val" style={{ color: '#60a5fa' }}>{stats?.sold_products ?? 0}</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Purchased by consumers</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Active Warranties</span>
            <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="stat-val" style={{ color: '#34d399' }}>{stats?.active_warranties ?? 0}</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Registered warranties</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Verification Scans</span>
            <div className="stat-icon" style={{ background: 'rgba(14, 165, 233, 0.15)', color: '#38bdf8' }}>
              <QrCode size={18} />
            </div>
          </div>
          <div className="stat-val" style={{ color: '#38bdf8' }}>{stats?.total_external_scans ?? 0}</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Pre-purchase checks</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Suspicious Events</span>
            <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#f87171' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="stat-val" style={{ color: stats?.total_suspicious_events ? '#f87171' : 'var(--text-primary)' }}>
            {stats?.total_suspicious_events ?? 0}
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Flags, mismatches & invalid</span>
        </div>
      </div>

      {/* Quick Actions & Recent Scans */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {/* Recent Scan History */}
        <div className="card">
          <div className="card-title-bar">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={18} color="#818cf8" /> Recent Verification Activity
            </h3>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('scans')}>
              View All Scans &rarr;
            </button>
          </div>

          {recentScans.length === 0 ? (
            <div className="state-box" style={{ padding: '2rem 1rem' }}>
              <p>No verification scans recorded yet.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Result</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentScans.map((scan) => (
                    <tr key={scan.scan_id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{scan.product_name || 'Unknown Item'}</div>
                        <div className="mono" style={{ color: 'var(--text-muted)' }}>{scan.product_id || 'Invalid Token'}</div>
                      </td>
                      <td>
                        <span className={`badge ${scan.result}`}>
                          {scan.result}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {new Date(scan.scanned_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Quick Demo Controls */}
        <div className="card">
          <div className="card-title-bar">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Package size={18} color="#34d399" /> System Controls & Navigation
            </h3>
          </div>

          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
            ProdVerify links physical products to immutable central registry records via dual cryptographically secure QR codes.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <button className="btn btn-primary" onClick={() => onNavigate('products')} style={{ justifyContent: 'flex-start' }}>
              <Package size={16} /> Manage Products & Generate QR Codes
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate('warranties')} style={{ justifyContent: 'flex-start' }}>
              <ShieldCheck size={16} /> View Warranty Registrations
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate('scans')} style={{ justifyContent: 'flex-start' }}>
              <Clock size={16} /> Inspect Audit & Scan Logs
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate('verify')} style={{ justifyContent: 'flex-start' }}>
              <ExternalLink size={16} /> Open Customer Verification Portal
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
