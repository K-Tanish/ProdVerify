import React, { useEffect, useState } from 'react';
import { api, RegistrationInfo, RegistrationSuccessResponse, Retailer } from '../api';
import { ShieldCheck, CheckCircle2, AlertTriangle, Package, Calendar } from 'lucide-react';

interface CustomerRegisterViewProps {
  initialToken?: string;
  onNavigateHome: () => void;
}

export const CustomerRegisterView: React.FC<CustomerRegisterViewProps> = ({ initialToken, onNavigateHome }) => {
  const [tokenInput, setTokenInput] = useState(initialToken || '');
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [productInfo, setProductInfo] = useState<RegistrationInfo | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [customerName, setCustomerName] = useState('');
  const [email, setEmail] = useState('');
  const [retailerId, setRetailerId] = useState<number | ''>('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [purchaseDate, setPurchaseDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [submitting, setSubmitting] = useState(false);

  // Success Confirmation State
  const [successData, setSuccessData] = useState<RegistrationSuccessResponse | null>(null);

  useEffect(() => {
    api.getRetailers().then(setRetailers).catch(console.error);
  }, []);

  const loadProductEligibility = async (tokenToUse: string) => {
    if (!tokenToUse.trim()) return;

    setLoading(true);
    setError(null);
    setSuccessData(null);
    try {
      const info = await api.getRegistrationInfo(tokenToUse.trim());
      setProductInfo(info);
      if (info.intended_retailer_id) {
        setRetailerId(info.intended_retailer_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to resolve internal registration token');
      setProductInfo(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialToken) {
      setTokenInput(initialToken);
      loadProductEligibility(initialToken);
    }
  }, [initialToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim() || retailerId === '') return;

    setSubmitting(true);
    setError(null);
    try {
      const res = await api.registerWarranty(tokenInput.trim(), {
        customer_name: customerName.trim(),
        email: email.trim(),
        retailer_id: Number(retailerId),
        purchase_price: purchasePrice ? parseFloat(purchasePrice) : null,
        purchase_date: purchaseDate,
      });
      setSuccessData(res);
      setProductInfo(null);
    } catch (err: any) {
      setError(err.message || 'Warranty registration failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
        <h1 className="page-title" style={{ fontSize: '2rem' }}>
          Warranty Registration & Activation
        </h1>
        <p className="page-subtitle">
          Activate manufacturer warranty using the unique internal security code found inside packaging.
        </p>
      </div>

      {/* Token Selector / Demo Presets */}
      {!successData && (
        <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              loadProductEligibility(tokenInput);
            }}
          >
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <input
                type="text"
                placeholder="Enter internal warranty token..."
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
                Find Product
              </button>
            </div>
          </form>

          {/* Presets */}
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>
            Quick Internal Token Demos:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                api.getProducts().then((prods) => {
                  if (prods[0]) {
                    setTokenInput(prods[0].internal_qr_token);
                    loadProductEligibility(prods[0].internal_qr_token);
                  }
                });
              }}
            >
              Product A Internal QR
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                api.getProducts().then((prods) => {
                  if (prods[1]) {
                    setTokenInput(prods[1].internal_qr_token);
                    loadProductEligibility(prods[1].internal_qr_token);
                  }
                });
              }}
            >
              Product B Internal QR
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                api.getProducts().then((prods) => {
                  if (prods[2]) {
                    setTokenInput(prods[2].internal_qr_token);
                    loadProductEligibility(prods[2].internal_qr_token);
                  }
                });
              }}
            >
              Product C Internal QR
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="state-box">
          <div className="spinner"></div>
          <p>Verifying internal token eligibility in registry...</p>
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={18} />
          <div>{error}</div>
        </div>
      )}

      {/* Success Confirmation Card */}
      {successData && (
        <div
          style={{
            background: 'var(--status-verified-bg)',
            border: '1px solid var(--status-verified-border)',
            borderRadius: '18px',
            padding: '2.5rem 1.75rem',
            textAlign: 'center',
            boxShadow: '0 10px 30px -10px rgba(16, 185, 129, 0.25)',
          }}
        >
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.2)',
              color: '#10b981',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
            }}
          >
            <CheckCircle2 size={42} />
          </div>

          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399', marginBottom: '0.5rem' }}>
            Warranty Activated Successfully
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.75rem' }}>
            Your registration is complete. Product status has transitioned to SOLD in the manufacturer registry.
          </p>

          <div
            style={{
              background: 'rgba(0, 0, 0, 0.35)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '12px',
              padding: '1.25rem',
              textAlign: 'left',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem',
              marginBottom: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Registration ID</span>
              <span className="mono" style={{ fontWeight: 700, color: '#818cf8' }}>
                #{successData.registration.registration_id}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Product</span>
              <span style={{ fontWeight: 700 }}>
                {successData.product.product_name} ({successData.product.serial_number})
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Registered Owner</span>
              <span style={{ fontWeight: 700 }}>
                {successData.registration.customer_name} ({successData.registration.email})
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Authorized Retailer</span>
              <span style={{ fontWeight: 700 }}>{successData.retailer.retailer_name}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Warranty Status</span>
              <span className="badge ACTIVE">ACTIVE</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Coverage Period</span>
              <span style={{ fontWeight: 700, color: '#34d399' }}>
                {successData.registration.warranty_start_date} to {successData.registration.warranty_end_date}
              </span>
            </div>
          </div>

          <button className="btn btn-primary" onClick={onNavigateHome}>
            Return to Manufacturer Portal
          </button>
        </div>
      )}

      {/* Registration Form Card */}
      {productInfo && !successData && !loading && (
        <div className="card">
          <div className="card-title-bar">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Package size={18} color="#818cf8" /> Eligible Product Unit
            </h3>
            <span className={`badge ${productInfo.product_status}`}>
              {productInfo.product_status}
            </span>
          </div>

          {/* Product details preview */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.75rem',
              background: 'rgba(0, 0, 0, 0.25)',
              padding: '1rem',
              borderRadius: '10px',
              marginBottom: '1.5rem',
            }}
          >
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Product Name</div>
              <div style={{ fontWeight: 600 }}>{productInfo.product_name}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Product ID</div>
              <div className="mono" style={{ fontWeight: 600 }}>{productInfo.product_id}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Serial Number</div>
              <div className="mono" style={{ fontWeight: 600 }}>{productInfo.serial_number}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Manufacturing Location</div>
              <div style={{ fontWeight: 600 }}>{productInfo.manufacturing_location || 'Not specified'}</div>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Full Customer Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. John Doe"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Email Address *</label>
              <input
                type="email"
                required
                placeholder="e.g. john.doe@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Purchased From Retailer *</label>
              <select
                required
                value={retailerId}
                onChange={(e) => setRetailerId(Number(e.target.value))}
              >
                <option value="">-- Select Store --</option>
                {retailers.map((r) => (
                  <option key={r.retailer_id} value={r.retailer_id}>
                    {r.retailer_name} ({r.city}, {r.state})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Purchase Price ($ USD)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="e.g. 299.99"
                  value={purchasePrice}
                  onChange={(e) => setPurchasePrice(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Purchase Date *</label>
                <input
                  type="date"
                  required
                  value={purchaseDate}
                  onChange={(e) => setPurchaseDate(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
              style={{ width: '100%', marginTop: '0.75rem', padding: '0.85rem' }}
            >
              <ShieldCheck size={18} />
              {submitting ? 'Activating Warranty in Registry...' : 'Register & Activate Warranty'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
