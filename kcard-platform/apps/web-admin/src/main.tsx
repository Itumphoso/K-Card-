import React from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  const cards = ['Users', 'Merchants', 'Vehicles', 'Transactions', 'Payouts', 'Credit Lines'];
  return <div className="page"><h1>K-Card Admin Dashboard</h1><div className="grid">{cards.map(c => <div className="card" key={c}>{c}</div>)}</div></div>;
}

createRoot(document.getElementById('root')!).render(<App />);
