import { useState, useEffect } from "react";

function App() {
  const [region, setRegion] = useState("Tokyo");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [insights, setInsights] = useState<any[]>([]);
  const [telemetry, setTelemetry] = useState({ harvesters: 0, records_ingested: 0 });

  const fetchInsights = async () => {
    try {
      const res = await fetch("/api/v1/insights");
      const data = await res.json();
      if (data.insights) setInsights(data.insights);
      
      const telRes = await fetch("/api/v1/telemetry");
      const telData = await telRes.json();
      if (telData) setTelemetry(telData);
    } catch (e) {
      console.error("Error fetching data:", e);
    }
  };

  useEffect(() => {
    fetchInsights();
    const interval = setInterval(fetchInsights, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await fetch("/api/v1/analyze-tourism", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region, query })
      });
      await fetchInsights();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="min-h-full">
      {/* Top navigation */}
      <header className="sticky top-0 z-10 border-b border-white/10 bg-base/60 backdrop-blur-md">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/20 text-accent">
              {/* compass mark */}
              <span className="text-lg font-bold">◈</span>
            </div>
            <div className="leading-tight">
              <div className="text-lg font-semibold tracking-tight text-white">
                Shirube&nbsp;AI
              </div>
              <div className="text-xs text-slate-400">
                Tourism &amp; Economic Decision Intelligence
              </div>
            </div>
          </div>

          <div className="hidden items-center gap-6 text-sm text-slate-300 sm:flex">
            <a className="transition hover:text-white" href="#">Dashboard</a>
            <a className="transition hover:text-white" href="#">Harvesters</a>
            <a className="transition hover:text-white" href="#">Insights</a>
          </div>
        </nav>
      </header>

      {/* Main dashboard area */}
      <main className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-white">Regional Overview</h1>
          <p className="mt-1 text-sm text-slate-400">
            Structured tourism &amp; economic signals for infrastructure decisions.
          </p>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          
          {/* Panel 1: Trigger Form */}
          <div className="glass p-6 md:col-span-1">
            <h2 className="text-lg font-medium text-white mb-4">Run Analysis</h2>
            <form onSubmit={handleRunAnalysis} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Region</label>
                <input 
                  type="text" 
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-accent"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Specific Query (Optional)</label>
                <input 
                  type="text" 
                  value={query}
                  placeholder="e.g. Find trending nightlife"
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-accent"
                />
              </div>
              <button 
                type="submit" 
                disabled={loading}
                className="w-full bg-accent/20 hover:bg-accent/30 text-accent font-medium py-2 rounded-lg transition"
              >
                {loading ? "Agents Harvesting..." : "Deploy Harvesters"}
              </button>
            </form>
            
            <div className="mt-8 pt-6 border-t border-white/10">
              <h3 className="text-sm font-medium text-slate-300 mb-3">System Telemetry</h3>
              <div className="flex justify-between text-sm text-slate-400 mb-2">
                <span>Active Harvesters:</span>
                <span className="text-white">{telemetry.harvesters}</span>
              </div>
              <div className="flex justify-between text-sm text-slate-400">
                <span>Records Ingested:</span>
                <span className="text-white">{telemetry.records_ingested}</span>
              </div>
            </div>
          </div>

          {/* Panel 2 & 3: Insights Feed */}
          <div className="glass p-6 md:col-span-2">
            <h2 className="text-lg font-medium text-white mb-4">Live Insights Feed</h2>
            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
              {insights.length === 0 ? (
                <div className="text-slate-500 text-center py-10">No insights harvested yet.</div>
              ) : (
                insights.map((insight, i) => (
                  <div key={i} className="bg-black/20 border border-white/5 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold px-2 py-1 bg-accent/20 text-accent rounded-full">
                        {insight.region}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(insight.harvested_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-sm text-slate-300 whitespace-pre-wrap">
                      {insight.insight}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          
        </div>
      </main>
    </div>
  );
}

export default App;
