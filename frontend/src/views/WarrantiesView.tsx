import React, { useEffect, useState } from 'react';
import { api, Warranty } from '../api';
import { Search, RefreshCw, ShieldCheck } from 'lucide-react';

export const WarrantiesView: React.FC = () => {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const loadWarranties = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getWarranties(statusFilter);
      setWarranties(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load warranties');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWarranties();
  }, [statusFilter]);

  const filteredWarranties = warranties.filter((w) => {
    const term = searchTerm.toLowerCase();
    const matchesCust = w.customer_name.toLowerCase().includes(term);
    const matchesEmail = w.email.toLowerCase().includes(term);
    const matchesProd = (w.product_name || '').toLowerCase().includes(term);
    const matchesSerial = (w.serial_number || '').toLowerCase().includes(term);
    const matchesRetailer = (w.retailer?.retailer_name || '').toLowerCase().includes(term);
    return matchesCust || matchesEmail || matchesProd || matchesSerial || matchesRetailer;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Warranty Registrations</h1>
          <p className="page-subtitle">
            Consumer warranty activations and registered physical product ownership
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadWarranties}>
          <RefreshCw size={15} /> Refresh List
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        {/* Filter bar */}
        <div className="filter-bar">
          <div className="search-input-wrap">
            <Search className="search-icon" size={16} />
            <input
              type="text"
              placeholder="Search by customer name, email, product, retailer..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            className="select-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Warranty Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="EXPIRED">EXPIRED</option>
            <option value="VOID">VOID</option>
          </select>
        </div>

        {/* Warranties Table */}
        {loading && warranties.length === 0 ? (
          <div className="state-box">
            <div className="spinner"></div>
            <p>Loading registered warranty records...</p>
          </div>
        ) : filteredWarranties.length === 0 ? (
          <div className="state-box">
            <ShieldCheck size={36} color="var(--text-muted)" />
            <p>No warranty registrations found matching criteria.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Reg ID</th>
                  <th>Product & Serial</th>
                  <th>Customer</th>
                  <th>Purchased From</th>
                  <th>Purchase Date & Price</th>
                  <th>Status</th>
                  <th>Warranty Coverage</th>
                </tr>
              </thead>
              <tbody>
                {filteredWarranties.map((w) => (
                  <tr key={w.registration_id}>
                    <td className="mono" style={{ color: '#818cf8', fontWeight: 700 }}>
                      #{w.registration_id}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{w.product_name}</div>
                      <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {w.product_id} &bull; {w.serial_number}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{w.customer_name}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{w.email}</div>
                    </td>
                    <td>
                      <div>{w.retailer?.retailer_name || 'Direct'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {w.retailer?.city ? `${w.retailer.city}, ${w.retailer.state}` : ''}
                      </div>
                    </td>
                    <td>
                      <div>{w.purchase_date}</div>
                      <div style={{ fontSize: '0.78rem', color: '#34d399', fontWeight: 600 }}>
                        {w.purchase_price ? `$${w.purchase_price.toFixed(2)}` : 'N/A'}
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${w.warranty_status}`}>{w.warranty_status}</span>
                    </td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      <div>{w.warranty_start_date} <span style={{ color: 'var(--text-muted)' }}>to</span></div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{w.warranty_end_date}</div>
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
