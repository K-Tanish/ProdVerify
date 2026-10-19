import React, { useEffect, useState } from 'react';
import { api, Product, Retailer } from '../api';
import { 
  Package, 
  Search, 
  Plus, 
  Download, 
  ExternalLink, 
  X, 
  RefreshCw,
  QrCode
} from 'lucide-react';

interface ProductsViewProps {
  onVerifyToken: (token: string) => void;
  onRegisterToken: (token: string) => void;
}

export const ProductsView: React.FC<ProductsViewProps> = ({ onVerifyToken, onRegisterToken }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // New Product Form
  const [formName, setFormName] = useState('');
  const [formRetailerId, setFormRetailerId] = useState<number | ''>('');
  const [formSerial, setFormSerial] = useState('');
  const [formLocation, setFormLocation] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [prods, rets] = await Promise.all([
        api.getProducts(),
        api.getRetailers(),
      ]);
      setProducts(prods);
      setRetailers(rets);
      if (rets.length > 0 && formRetailerId === '') {
        setFormRetailerId(rets[0].retailer_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || formRetailerId === '') return;

    setCreating(true);
    setCreateError(null);
    try {
      await api.createProduct({
        product_name: formName.trim(),
        intended_retailer_id: Number(formRetailerId),
        serial_number: formSerial.trim() || undefined,
        manufacturing_location: formLocation.trim() || undefined,
      });
      setIsCreateOpen(false);
      setFormName('');
      setFormSerial('');
      setFormLocation('');
      await loadData();
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create product');
    } finally {
      setCreating(false);
    }
  };

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      p.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.product_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.intended_retailer?.retailer_name || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || p.product_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Product Registry & QR Management</h1>
          <p className="page-subtitle">
            Manage authenticated items, generate dual QR codes, and review distribution channels
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={loadData}>
            <RefreshCw size={15} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
            <Plus size={16} /> Register New Product
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        {/* Filter bar */}
        <div className="filter-bar">
          <div className="search-input-wrap">
            <Search className="search-icon" size={16} />
            <input
              type="text"
              placeholder="Search by product name, ID, serial number, retailer..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            className="select-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            <option value="IN_STOCK">IN_STOCK</option>
            <option value="SOLD">SOLD</option>
            <option value="BLOCKED">BLOCKED</option>
          </select>
        </div>

        {/* Product Table */}
        {loading && products.length === 0 ? (
          <div className="state-box">
            <div className="spinner"></div>
            <p>Loading registered products...</p>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="state-box">
            <Package size={36} color="var(--text-muted)" />
            <p>No products match your search or filter criteria.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Serial Number</th>
                  <th>Intended Retailer</th>
                  <th>Status</th>
                  <th>Warranty</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((p) => (
                  <tr key={p.product_id}>
                    <td>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{p.product_name}</div>
                      <div className="mono" style={{ color: '#818cf8', fontSize: '0.78rem' }}>{p.product_id}</div>
                    </td>
                    <td className="mono">{p.serial_number}</td>
                    <td>
                      <div>{p.intended_retailer?.retailer_name || 'Unassigned'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {p.intended_retailer?.city ? `${p.intended_retailer.city}, ${p.intended_retailer.state}` : ''}
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${p.product_status}`}>
                        {p.product_status}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${p.registration_status === 'REGISTERED' ? 'ACTIVE' : 'SUSPICIOUS'}`} style={{ fontSize: '0.72rem' }}>
                        {p.registration_status}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelectedProduct(p)}
                        style={{ marginRight: '0.4rem' }}
                      >
                        <QrCode size={14} /> Preview & Download QRs
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* QR Preview & Download Modal */}
      {selectedProduct && (
        <div className="modal-backdrop" onClick={() => setSelectedProduct(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                  QR Codes for {selectedProduct.product_name}
                </h2>
                <div className="mono" style={{ color: '#818cf8', fontSize: '0.8rem', marginTop: '0.2rem' }}>
                  ID: {selectedProduct.product_id} &bull; SN: {selectedProduct.serial_number}
                </div>
              </div>
              <button className="modal-close" onClick={() => setSelectedProduct(null)}>
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Each unit has two cryptographically distinct tokens. Download separate high-resolution PNG images for packaging print.
            </p>

            <div className="qr-preview-grid">
              {/* External QR */}
              <div className="qr-box">
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>
                  External QR (Verification)
                </span>
                <img
                  src={api.getQrImageUrl(selectedProduct.product_id, 'external')}
                  alt="External QR"
                />
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Printed on packaging exterior
                </div>
                <div style={{ display: 'flex', gap: '0.4rem', width: '100%' }}>
                  <a
                    href={api.getQrDownloadUrl(selectedProduct.product_id, 'external')}
                    className="btn btn-secondary btn-sm"
                    style={{ flex: 1 }}
                    download
                  >
                    <Download size={13} /> Download
                  </a>
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ flex: 1 }}
                    onClick={() => {
                      onVerifyToken(selectedProduct.external_qr_token);
                      setSelectedProduct(null);
                    }}
                  >
                    <ExternalLink size={13} /> Test
                  </button>
                </div>
              </div>

              {/* Internal QR */}
              <div className="qr-box">
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase' }}>
                  Internal QR (Registration)
                </span>
                <img
                  src={api.getQrImageUrl(selectedProduct.product_id, 'internal')}
                  alt="Internal QR"
                />
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  Placed inside security seal
                </div>
                <div style={{ display: 'flex', gap: '0.4rem', width: '100%' }}>
                  <a
                    href={api.getQrDownloadUrl(selectedProduct.product_id, 'internal')}
                    className="btn btn-secondary btn-sm"
                    style={{ flex: 1 }}
                    download
                  >
                    <Download size={13} /> Download
                  </a>
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ flex: 1 }}
                    onClick={() => {
                      onRegisterToken(selectedProduct.internal_qr_token);
                      setSelectedProduct(null);
                    }}
                  >
                    <ExternalLink size={13} /> Test
                  </button>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setSelectedProduct(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Product Registration Modal */}
      {isCreateOpen && (
        <div className="modal-backdrop" onClick={() => setIsCreateOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Register New Product Unit</h2>
              <button className="modal-close" onClick={() => setIsCreateOpen(false)}>
                <X size={20} />
              </button>
            </div>

            {createError && <div className="alert alert-error">{createError}</div>}

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Product Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. UltraVision 4K Display"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Intended Authorized Retailer *</label>
                <select
                  required
                  value={formRetailerId}
                  onChange={(e) => setFormRetailerId(Number(e.target.value))}
                >
                  <option value="">-- Select Retailer --</option>
                  {retailers.map((r) => (
                    <option key={r.retailer_id} value={r.retailer_id}>
                      {r.retailer_name} ({r.city}, {r.state})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Custom Serial Number (Optional - auto-generated if left blank)</label>
                <input
                  type="text"
                  placeholder="e.g. SN-UV-2026-001"
                  value={formSerial}
                  onChange={(e) => setFormSerial(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Manufacturing Facility (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Fremont, CA"
                  value={formLocation}
                  onChange={(e) => setFormLocation(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsCreateOpen(false)}
                  disabled={creating}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Registering...' : 'Create & Generate QRs'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
