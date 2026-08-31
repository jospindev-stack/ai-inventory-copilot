import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Bot, Download, Package, Search, ShieldCheck, TrendingUp } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const riskOrder = { critical: 4, high: 3, medium: 2, low: 1 }

function formatCurrency(value) {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  }).format(value || 0)
}

function App() {
  const [summary, setSummary] = useState(null)
  const [products, setProducts] = useState([])
  const [risks, setRisks] = useState([])
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [selectedSku, setSelectedSku] = useState('')
  const [question, setQuestion] = useState('What should I prioritize for this item?')
  const [answer, setAnswer] = useState('')
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(true)
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const [summaryResponse, productsResponse, risksResponse] = await Promise.all([
          fetch(`${API_URL}/dashboard`),
          fetch(`${API_URL}/products`),
          fetch(`${API_URL}/risks`),
        ])

        if (!summaryResponse.ok || !productsResponse.ok || !risksResponse.ok) {
          throw new Error('Unable to load inventory data.')
        }

        const [summaryData, productsData, risksData] = await Promise.all([
          summaryResponse.json(),
          productsResponse.json(),
          risksResponse.json(),
        ])

        setSummary(summaryData)
        setProducts(productsData)
        setRisks(risksData)
        setSelectedSku(risksData[0]?.sku || '')
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  const rows = useMemo(() => {
    const productBySku = Object.fromEntries(products.map((product) => [product.sku, product]))

    return risks
      .map((risk) => ({ ...productBySku[risk.sku], ...risk }))
      .filter((item) => item.sku)
      .filter((item) => {
        const term = search.trim().toLowerCase()
        const matchesSearch = !term || item.sku.toLowerCase().includes(term) || item.name.toLowerCase().includes(term)
        const matchesRisk = riskFilter === 'all' || item.risk_level === riskFilter
        return matchesSearch && matchesRisk
      })
      .sort((a, b) => riskOrder[b.risk_level] - riskOrder[a.risk_level] || b.risk_score - a.risk_score)
  }, [products, risks, search, riskFilter])

  async function askCopilot(event) {
    event.preventDefault()
    if (!question.trim()) return

    setAsking(true)
    setAnswer('')
    setError('')

    try {
      const response = await fetch(`${API_URL}/copilot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, sku: selectedSku || null }),
      })

      if (!response.ok) throw new Error('The copilot request failed.')
      const data = await response.json()
      setAnswer(data.answer)
      setSource(data.source)
    } catch (err) {
      setError(err.message)
    } finally {
      setAsking(false)
    }
  }

  if (loading) return <main className="centered">Loading inventory data...</main>

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Manufacturing Operations</p>
          <h1>AI Inventory Copilot</h1>
          <p className="sidebar-copy">Inventory risk monitoring with explainable replenishment recommendations.</p>
        </div>
        <nav>
          <a className="active" href="#overview">Overview</a>
          <a href="#inventory">Inventory</a>
          <a href="#copilot">Copilot</a>
        </nav>
        <div className="sidebar-footer">FastAPI · React · Ollama</div>
      </aside>

      <main className="content">
        <header className="page-header" id="overview">
          <div>
            <p className="eyebrow">Inventory control</p>
            <h2>Stock risk overview</h2>
            <p>Prioritize material shortages before they affect production.</p>
          </div>
          <a className="button secondary" href={`${API_URL}/export`}>
            <Download size={17} /> Export report
          </a>
        </header>

        {error && <div className="error-banner">{error}</div>}

        <section className="kpi-grid">
          <Kpi icon={<Package size={20} />} label="Inventory items" value={summary?.total_items || 0} />
          <Kpi icon={<TrendingUp size={20} />} label="Inventory value" value={formatCurrency(summary?.inventory_value)} />
          <Kpi icon={<AlertTriangle size={20} />} label="Critical items" value={summary?.critical_items || 0} />
          <Kpi icon={<ShieldCheck size={20} />} label="Average risk" value={`${summary?.average_risk_score || 0}/100`} />
        </section>

        <section className="panel" id="inventory">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Priorities</p>
              <h3>Inventory risk register</h3>
            </div>
            <div className="filters">
              <label className="search-box">
                <Search size={16} />
                <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search SKU or item" />
              </label>
              <select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                <option value="all">All risk levels</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Item</th>
                  <th>On hand</th>
                  <th>Coverage</th>
                  <th>Lead time</th>
                  <th>Risk</th>
                  <th>Score</th>
                  <th>Order qty</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr key={item.sku} onClick={() => setSelectedSku(item.sku)} className={selectedSku === item.sku ? 'selected-row' : ''}>
                    <td className="mono">{item.sku}</td>
                    <td><strong>{item.name}</strong><span>{item.category}</span></td>
                    <td>{item.on_hand}</td>
                    <td>{item.days_of_cover} days</td>
                    <td>{item.lead_time_days} days</td>
                    <td><span className={`risk-badge ${item.risk_level}`}>{item.risk_level}</span></td>
                    <td>{item.risk_score}</td>
                    <td>{item.recommended_order_qty}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel copilot-panel" id="copilot">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Decision support</p>
              <h3>Inventory copilot</h3>
              <p>Ask for an explanation or replenishment recommendation for the selected item.</p>
            </div>
            <Bot size={28} />
          </div>

          <form onSubmit={askCopilot} className="copilot-form">
            <select value={selectedSku} onChange={(event) => setSelectedSku(event.target.value)}>
              {risks.map((risk) => <option key={risk.sku} value={risk.sku}>{risk.sku}</option>)}
            </select>
            <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about this inventory item" />
            <button className="button primary" disabled={asking}>{asking ? 'Analyzing...' : 'Ask copilot'}</button>
          </form>

          {answer && (
            <div className="answer-card">
              <p>{answer}</p>
              <span>Response source: {source === 'ollama' ? 'local Ollama model' : 'deterministic fallback'}</span>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

function Kpi({ icon, label, value }) {
  return (
    <article className="kpi-card">
      <div className="kpi-icon">{icon}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
    </article>
  )
}

export default App
