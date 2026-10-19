import { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Package, 
  Clock, 
  ShieldCheck, 
  Search, 
  UserCheck
} from 'lucide-react';
import { DashboardView } from './views/DashboardView';
import { ProductsView } from './views/ProductsView';
import { ScansView } from './views/ScansView';
import { WarrantiesView } from './views/WarrantiesView';
import { CustomerVerifyView } from './views/CustomerVerifyView';
import { CustomerRegisterView } from './views/CustomerRegisterView';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'products' | 'scans' | 'warranties' | 'verify' | 'register'>('dashboard');
  const [activeToken, setActiveToken] = useState<string>('');

  // Read URL query parameters on initial load for deep linking (e.g. ?tab=verify&token=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab');
    const tokenParam = params.get('token');

    if (tabParam && ['dashboard', 'products', 'scans', 'warranties', 'verify', 'register'].includes(tabParam)) {
      setActiveTab(tabParam as any);
    }
    if (tokenParam) {
      setActiveToken(tokenParam);
    }
  }, []);

  const handleVerifyToken = (token: string) => {
    setActiveToken(token);
    setActiveTab('verify');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRegisterToken = (token: string) => {
    setActiveToken(token);
    setActiveTab('register');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="app-layout">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand" onClick={() => setActiveTab('dashboard')}>
          <div className="nav-logo">
            <ShieldCheck size={22} color="white" />
          </div>
          <div className="brand-text">
            Prod<span>Verify</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-links">
          <button
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={16} /> Dashboard
          </button>

          <button
            className={`nav-btn ${activeTab === 'products' ? 'active' : ''}`}
            onClick={() => setActiveTab('products')}
          >
            <Package size={16} /> Products & QRs
          </button>

          <button
            className={`nav-btn ${activeTab === 'scans' ? 'active' : ''}`}
            onClick={() => setActiveTab('scans')}
          >
            <Clock size={16} /> Scan History
          </button>

          <button
            className={`nav-btn ${activeTab === 'warranties' ? 'active' : ''}`}
            onClick={() => setActiveTab('warranties')}
          >
            <ShieldCheck size={16} /> Warranties
          </button>

          <div style={{ width: '1px', height: '24px', background: 'var(--border-subtle)', margin: '0 0.25rem' }} />

          <button
            className={`nav-btn ${activeTab === 'verify' ? 'active' : ''}`}
            onClick={() => { setActiveToken(''); setActiveTab('verify'); }}
            style={{ color: activeTab === 'verify' ? '#ffffff' : '#38bdf8' }}
          >
            <Search size={16} /> Customer Verify
          </button>

          <button
            className={`nav-btn ${activeTab === 'register' ? 'active' : ''}`}
            onClick={() => { setActiveToken(''); setActiveTab('register'); }}
            style={{ color: activeTab === 'register' ? '#ffffff' : '#a78bfa' }}
          >
            <UserCheck size={16} /> Customer Register
          </button>
        </nav>

        {/* Demo Notice */}
        <div className="nav-badge-demo" title="Manufacturer endpoints separated. Production OAuth/JWT authentication can be plugged in without changing domain models.">
          Local MVP &bull; Auth Omitted
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'dashboard' && (
          <DashboardView onNavigate={(tab: any) => setActiveTab(tab)} onVerifyToken={handleVerifyToken} />
        )}

        {activeTab === 'products' && (
          <ProductsView onVerifyToken={handleVerifyToken} onRegisterToken={handleRegisterToken} />
        )}

        {activeTab === 'scans' && (
          <ScansView />
        )}

        {activeTab === 'warranties' && (
          <WarrantiesView />
        )}

        {activeTab === 'verify' && (
          <CustomerVerifyView initialToken={activeToken} />
        )}

        {activeTab === 'register' && (
          <CustomerRegisterView initialToken={activeToken} onNavigateHome={() => setActiveTab('dashboard')} />
        )}
      </main>

      {/* Footer */}
      <footer>
        ProdVerify MVP &bull; Anti-Counterfeit Dual-Token Architecture &bull; React + Vite + TypeScript &bull; Python FastAPI & SQLite
      </footer>
    </div>
  );
}

export default App;
