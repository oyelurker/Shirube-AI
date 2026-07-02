function App() {
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

        {/* Empty dashboard grid — cards to be populated from /api/v1 */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="glass flex h-40 items-center justify-center p-6 text-slate-500">
            No data yet
          </div>
          <div className="glass flex h-40 items-center justify-center p-6 text-slate-500">
            No data yet
          </div>
          <div className="glass flex h-40 items-center justify-center p-6 text-slate-500">
            No data yet
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
