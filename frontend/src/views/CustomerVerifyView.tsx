import React, { useEffect, useState } from 'react';
import { api, Retailer, VerificationResponse } from '../api';
import { 
  ShieldCheck, 
  AlertTriangle, 
  XCircle, 
  Store, 
  QrCode, 
  Search,
  CheckCircle2,
  HelpCircle
} from 'lucide-react';

interface CustomerVerifyViewProps {
  initialToken?: string;
}

export const CustomerVerifyView: React.FC<CustomerVerifyViewProps> = ({ initialToken }) => {
  const [tokenInput, setTokenInput] = useState(initialToken || '');
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [selectedRetailer, setSelectedRetailer] = useState<number | ''>('');
  
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load available retailers for self-reported check
  useEffect(() => {
    api.getRetailers().then(setRetailers).catch(console.error);
  }, []);

  const handleVerify = async (tokenToUse?: string, retailerIdToUse?: number | '') => {
    const targetToken = (tokenToUse !== undefined ? tokenToUse : tokenInput).trim();
    if (!targetToken) return;

    setLoading(true);
    setError(null);
    try {
      const activeRetId = retailerIdToUse !== undefined 
        ? (retailerIdToUse === '' ? null : Number(retailerIdToUse))
        : (selectedRetailer === '' ? null : Number(selectedRetailer));

      const res = await api.verifyToken(targetToken, activeRetId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Verification service could not be reached');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialToken) {
      setTokenInput(initialToken);
      handleVerify(initialToken);
    }
  }, [initialToken]);

  const onRetailerChange = (retId: number | '') => {
    setSelectedRetailer(retId);
    if (tokenInput.trim()) {
      handleVerify(tokenInput.trim(), retId);
    }
  };

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
        <h1 className="page-title" style={{ fontSize: '2rem' }}>
          Consumer Pre-Purchase Verification
        </h1>
        <p className="page-subtitle">
          Verify product authenticity against the manufacturer central registry before purchasing.
        </p>
      </div>

      {/* Token Input & Demo Scenarios Box */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <form onSubmit={(e) => { e.preventDefault(); handleVerify(); }}>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <input
              type="text"
              placeholder="Paste or enter external QR token..."
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                background: '#1e293b',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                color: 'var(--text-primary)',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '0.85rem',
                outline: 'none',
              }}
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !tokenInput.trim()}>
              <Search size={15} /> Verify
            </button>
          </div>
        </form>

        {/* Demo Preset Buttons */}
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>
          Quick Test Scenarios:
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              // Product A external token from seed
              api.getProducts().then((prods) => {
                if (prods[0]) {
                  setTokenInput(prods[0].external_qr_token);
                  handleVerify(prods[0].external_qr_token);
                }
              });
            }}
          >
            Product A (Genuine)
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              api.getProducts().then((prods) => {
                if (prods[1]) {
                  setTokenInput(prods[1].external_qr_token);
                  handleVerify(prods[1].external_qr_token);
                }
              });
            }}
          >
            Product B (Genuine)
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              const fake = 'INVALID-QR-COUNTERFEIT-TOKEN-999';
              setTokenInput(fake);
              handleVerify(fake);
            }}
          >
            Test Invalid Token
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              // Internal token to test mismatch
              api.getProducts().then((prods) => {
                if (prods[0]) {
                  setTokenInput(prods[0].internal_qr_token);
                  handleVerify(prods[0].internal_qr_token);
                }
              });
            }}
          >
            Internal Code Mismatch
          </button>
        </div>
      </div>

      {loading && (
        <div className="state-box">
          <div className="spinner"></div>
          <p>Contacting registry and checking risk indicators...</p>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {/* Verification Result Display */}
      {data && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Main Hero Result Box */}
          <div
            style={{
              borderRadius: '16px',
              padding: '2rem 1.5rem',
              textAlign: 'center',
              backdropFilter: 'blur(12px)',
              border: `1px solid ${
                data.result === 'VERIFIED'
                  ? 'var(--status-verified-border)'
                  : data.result === 'SUSPICIOUS'
                  ? 'var(--status-suspicious-border)'
                  : 'var(--status-invalid-border)'
              }`,
              background:
                data.result === 'VERIFIED'
                  ? 'var(--status-verified-bg)'
                  : data.result === 'SUSPICIOUS'
                  ? 'var(--status-suspicious-bg)'
                  : 'var(--status-invalid-bg)',
            }}
          >
            <div style={{ display: 'inline-flex', marginBottom: '1rem' }}>
              {data.result === 'VERIFIED' && <CheckCircle2 size={54} color="#10b981" />}
              {data.result === 'SUSPICIOUS' && <AlertTriangle size={54} color="#f59e0b" />}
              {data.result === 'INVALID' && <XCircle size={54} color="#ef4444" />}
            </div>

            <h2 style={{ fontSize: '1.65rem', fontWeight: 800, marginBottom: '0.5rem' }}>
              {data.result === 'VERIFIED' && 'Authentic Product Confirmed'}
              {data.result === 'SUSPICIOUS' && 'Caution: Security Warning'}
              {data.result === 'INVALID' && 'Invalid / Unrecognized Code'}
            </h2>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.5, maxWidth: '520px', margin: '0 auto' }}>
              {data.explanation}
            </p>

            {/* Warnings list if any */}
            {data.risk_warnings && data.risk_warnings.length > 0 && (
              <div
                style={{
                  marginTop: '1.25rem',
                  padding: '1rem',
                  borderRadius: '10px',
                  background: 'rgba(0, 0, 0, 0.4)',
                  textAlign: 'left',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', color: '#f59e0b', marginBottom: '0.4rem' }}>
                  Risk Indicators Requiring Attention
                </div>
                {data.risk_warnings.map((w, idx) => (
                  <div key={idx} style={{ fontSize: '0.85rem', color: '#f3f4f6', lineHeight: 1.45, marginBottom: '0.3rem' }}>
                    &bull; {w}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Verification Scan Counter */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.85rem 1.25rem',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              <QrCode size={18} color="#818cf8" />
              External Verification Scan Count
            </div>
            <div className="mono" style={{ fontWeight: 700, color: '#818cf8', background: 'rgba(99, 102, 241, 0.15)', padding: '0.2rem 0.6rem', borderRadius: '6px' }}>
              {data.scan_count} {data.scan_count === 1 ? 'scan' : 'scans'}
            </div>
          </div>

          {/* Product Details Card */}
          {data.product && (
            <div className="card">
              <div className="card-title-bar">
                <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck size={18} color="#34d399" /> Registered Product Identity
                </h3>
                <span className={`badge ${data.product.product_status}`}>
                  {data.product.product_status}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Product Name</div>
                  <div style={{ fontWeight: 600 }}>{data.product.product_name}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Product ID</div>
                  <div className="mono" style={{ fontWeight: 600 }}>{data.product.product_id}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Serial Number</div>
                  <div className="mono" style={{ fontWeight: 600 }}>{data.product.serial_number}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Manufacturing Location</div>
                  <div style={{ fontWeight: 600 }}>{data.product.manufacturing_location || 'Not specified'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Warranty Status</div>
                  <div style={{ fontWeight: 600 }}>{data.product.registration_status}</div>
                </div>
              </div>
            </div>
          )}

          {/* Retailer Location Check Card */}
          {data.intended_retailer && (
            <div className="card">
              <div className="card-title-bar">
                <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Store size={18} color="#818cf8" /> Authorized Distribution Store
                </h3>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontWeight: 600, fontSize: '1.05rem' }}>{data.intended_retailer.retailer_name}</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {data.intended_retailer.address ? `${data.intended_retailer.address}, ` : ''}
                  {data.intended_retailer.city}, {data.intended_retailer.state}
                </div>
              </div>

              {/* Location Verification Tool */}
              <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '1rem', borderRadius: '10px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Verify Current Store (Self-Reported Evidence)
                </label>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  Confirm where you are buying this item. ProdVerify compares your selected store with the manufacturer distribution channel.
                </p>
                <select
                  value={selectedRetailer}
                  onChange={(e) => onRetailerChange(e.target.value === '' ? '' : Number(e.target.value))}
                  style={{
                    width: '100%',
                    padding: '0.65rem 1rem',
                    background: '#1e293b',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)',
                    fontSize: '0.88rem',
                    outline: 'none',
                  }}
                >
                  <option value="">-- Select Store Where You Are Purchasing --</option>
                  {retailers.map((r) => (
                    <option key={r.retailer_id} value={r.retailer_id}>
                      {r.retailer_name} ({r.city}, {r.state})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Authenticity Disclaimer */}
          <div
            style={{
              padding: '1rem 1.25rem',
              borderRadius: '12px',
              background: 'rgba(15, 23, 42, 0.5)',
              border: '1px dashed rgba(255, 255, 255, 0.12)',
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              lineHeight: 1.5,
            }}
          >
            <div style={{ fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <HelpCircle size={14} /> Authenticity Assurance Disclaimer
            </div>
            {data.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
