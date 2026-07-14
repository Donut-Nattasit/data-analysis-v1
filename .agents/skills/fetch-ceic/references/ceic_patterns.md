# CEIC Search & Database Prioritization

## Database hierarchy

1. **World Trend Plus (WTP) / Global Economic Monitor (GEM)** — default first choice.
   - Use for cross-country comparisons, regional analysis (ASEAN, G20), standardized macro benchmarks.
   - GEM series are harmonized by CEIC experts for methodological consistency across countries.
   - Naming pattern: `[Metric]: [Sub-metric]: [Frequency]: [Country]` (e.g. `Real GDP: YoY: Quarterly: Thailand`).
   - Always search here first for GDP, CPI, and standard unemployment data.
2. **China Premium Database** — for China provincial data, specific industry sectors, or high-frequency national indicators not in GEM.
3. **Global Database** — standard national-level data when GEM is unavailable; original series as reported by national source agencies. Use for specialized indicators (e.g. "Thailand Public Debt to GDP") or detailed balance-of-payments components.
4. **Daily Database** — financial markets, exchange rates, commodity prices (e.g. "Gold Prices", "Stock Indices").

## Search heuristics

- **Eliminating "trade partner" noise**: searching "Exports: China" often returns "Exports: to China" from other countries. Append `fob`, `Customs Basis`, or `Total` to the keyword, or use `Exports: fob: [Country]` / `Trade Balance: Export: [Country]`. Be wary of names containing `to`, `from`, `partner`, `destination` unless bilateral trade is specifically wanted.
- **Frequency**: for GDP always include `Quarterly` or `Annual` in the keyword; for inflation/trade include `Monthly`.
- **Real vs Nominal**: prioritize `Real`/`Constant Prices` for growth analysis; `Nominal`/`Current Prices` for ratio analysis (e.g. Debt/GDP).
- **YoY vs Index**: prioritize `YoY` series for growth charts; if only `Index` is available, note that a separate growth-rate calculation will be needed downstream.
- **GEM naming pattern matching**: GEM series follow `Category: Sub-category: Frequency: Country`. To find the same series across countries: search `[Metric]: [Sub-category]: [Frequency]: [Country A]`, extract the prefix (`[Metric]: [Sub-category]: [Frequency]:`), then search `[Prefix] [Country B]`, `[Prefix] [Country C]`, etc.
  - Examples: `Real GDP: YoY: Quarterly: Indonesia`, `Consumer Price Index: YoY: Monthly: Philippines`, `Exports: fob: Monthly: Malaysia`.
