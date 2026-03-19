"""
Blockarb — Spread Fetcher Web App (Mobile Optimised)
======================================================
Run:
    pip install ccxt flask
    python blockarb_spread_app.py
"""

import os
from flask import Flask, jsonify, render_template_string
import ccxt, time
from itertools import combinations
from datetime import datetime

app = Flask(__name__)

SYMBOLS = ["BTC/USDT", "ETH/USDT", "USDT/USD"]

EXCHANGES = {
    "OKX":      ccxt.okx(),
    "Kraken":   ccxt.kraken(),
    "Coinbase": ccxt.coinbase(),
    "Gate.io":  ccxt.gateio(),
    "Bitfinex": ccxt.bitfinex(),
    "Huobi":    ccxt.huobi(),
    "KuCoin":   ccxt.kucoin(),
}

SYMBOL_MAP = {
    "Kraken":   {"BTC/USDT": "BTC/USD",  "ETH/USDT": "ETH/USD",  "USDT/USD": "USDT/USD"},
    "Coinbase": {"BTC/USDT": "BTC/USD",  "ETH/USDT": "ETH/USD",  "USDT/USD": "USDT/USD"},
    "Bitfinex": {"BTC/USDT": "BTC/USDT", "ETH/USDT": "ETH/USDT", "USDT/USD": "USDT/USD"},
}

def fetch_top_of_book(exchange_name, exchange, symbol):
    try:
        sym = SYMBOL_MAP.get(exchange_name, {}).get(symbol, symbol)
        ticker = exchange.fetch_ticker(sym)
        bid, ask = ticker.get("bid"), ticker.get("ask")
        if bid and ask:
            return float(bid), float(ask)
    except:
        return None

def calc_spread(bid, ask):
    mid = (bid + ask) / 2
    return round(((ask - bid) / mid) * 100, 4)

def fetch_all_spreads():
    results = []
    timestamp = datetime.utcnow().strftime("%d %b %Y · %H:%M UTC")

    for symbol in SYMBOLS:
        books = {}
        exchange_data = []

        for name, exchange in EXCHANGES.items():
            result = fetch_top_of_book(name, exchange, symbol)
            if result:
                bid, ask = result
                books[name] = {"bid": bid, "ask": ask}
                exchange_data.append({"name": name, "bid": bid, "ask": ask})
            time.sleep(0.12)

        pairs = []
        best_spread = None
        best_pair = None

        if len(books) >= 2:
            for (ex_a, ex_b) in combinations(books.keys(), 2):
                spread = calc_spread(books[ex_a]["bid"], books[ex_b]["ask"])
                pairs.append({
                    "label": f"{ex_a} / {ex_b}",
                    "spread": spread,
                    "direction": "pos" if spread > 0 else ("neg" if spread < 0 else "flat")
                })
                if best_spread is None or abs(spread) > abs(best_spread):
                    best_spread = spread
                    best_pair = f"{ex_a} / {ex_b}"

        pairs.sort(key=lambda x: abs(x["spread"]), reverse=True)

        results.append({
            "symbol": symbol,
            "exchanges": exchange_data,
            "pairs": pairs,
            "best_spread": best_spread,
            "best_pair": best_pair,
        })

    return {"timestamp": timestamp, "data": results}


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#070a0d">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>BlockArb · Spreads</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

:root {
  --bg:      #070a0d;
  --s1:      #0c1117;
  --s2:      #111820;
  --border:  rgba(255,255,255,0.07);
  --accent:  #00ffb3;
  --text:    #c8d8e4;
  --muted:   #3d5566;
  --muted2:  #567080;
  --pos:     #00ffb3;
  --neg:     #ff4d6a;
  --flat:    #3d5566;
  --display: 'Barlow Condensed', sans-serif;
  --mono:    'IBM Plex Mono', monospace;
}

html, body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--mono);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  overscroll-behavior: none;
}

/* HEADER */
.header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(7,10,13,0.96);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 14px 16px 12px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.wordmark { font-family: var(--display); font-weight: 800; font-size: 22px; letter-spacing: -0.5px; color: #fff; line-height: 1; }
.wordmark em { font-style: normal; color: var(--accent); }
.wordmark-sub { font-family: var(--mono); font-size: 9px; letter-spacing: 2.5px; text-transform: uppercase; color: var(--muted2); margin-top: 2px; }

.fetch-btn {
  all: unset; cursor: pointer;
  display: flex; align-items: center; gap: 7px;
  background: var(--accent); color: #000;
  font-family: var(--display); font-weight: 700; font-size: 15px; letter-spacing: 0.3px;
  padding: 10px 18px; border-radius: 8px;
  white-space: nowrap; min-height: 44px;
  transition: transform 0.12s, opacity 0.12s;
}
.fetch-btn:active { transform: scale(0.95); opacity: 0.8; }
.fetch-btn:disabled { opacity: 0.35; pointer-events: none; }
.fetch-btn.loading svg { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* STATUS */
.status-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 16px; min-height: 32px;
  font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
  color: var(--muted); border-bottom: 1px solid var(--border);
}
.status-bar.live { color: var(--accent); }
.status-bar.err  { color: var(--neg); }
.pulse { display: inline-flex; width: 5px; height: 5px; border-radius: 50%; background: var(--accent); animation: blink 1.2s ease infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.1} }

/* CONTENT */
.content { padding: 12px 12px 24px; display: flex; flex-direction: column; gap: 12px; }

/* EMPTY */
.empty { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; gap: 10px; color: var(--muted); }
.empty-icon { font-size: 36px; margin-bottom: 4px; opacity: 0.4; }
.empty-title { font-family: var(--display); font-size: 16px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--muted2); }
.empty-sub { font-size: 11px; letter-spacing: 1px; text-align: center; line-height: 1.8; }

/* CARD */
.card { background: var(--s1); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; animation: rise 0.3s ease both; }
@keyframes rise { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }

.card-head {
  padding: 12px 14px 10px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border);
  background: var(--s2);
}
.asset-name { font-family: var(--display); font-weight: 800; font-size: 20px; letter-spacing: -0.3px; color: #fff; }
.best-chip {
  display: flex; align-items: center; gap: 5px;
  background: rgba(0,255,179,0.07); border: 1px solid rgba(0,255,179,0.18);
  border-radius: 6px; padding: 4px 9px;
  font-family: var(--mono); font-size: 11px; font-weight: 600; color: var(--accent);
}
.best-chip.neg { background: rgba(255,77,106,0.07); border-color: rgba(255,77,106,0.18); color: var(--neg); }

/* BOOK */
.book-section { padding: 10px 14px; border-bottom: 1px solid var(--border); }
.section-label { font-size: 8px; letter-spacing: 2.5px; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
.book-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.book-item { background: var(--s2); border: 1px solid var(--border); border-radius: 7px; padding: 8px 10px; }
.book-item-name { font-family: var(--display); font-weight: 600; font-size: 12px; letter-spacing: 0.5px; color: var(--muted2); text-transform: uppercase; margin-bottom: 5px; }
.book-price-row { display: flex; align-items: center; justify-content: space-between; font-size: 11px; margin-bottom: 2px; }
.price-tag { color: var(--muted); font-size: 9px; letter-spacing: 1px; }
.price-val { font-weight: 500; color: var(--text); font-size: 12px; }

/* SPREADS */
.spreads-section { padding: 10px 14px 12px; }
.spread-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.03); gap: 10px; }
.spread-row:last-child { border-bottom: none; }
.spread-pair { font-size: 11px; color: var(--muted2); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.spread-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.spread-val { font-family: var(--mono); font-weight: 600; font-size: 13px; letter-spacing: -0.3px; }
.spread-val.pos  { color: var(--pos); }
.spread-val.neg  { color: var(--neg); }
.spread-val.flat { color: var(--flat); }
.best-star { font-size: 9px; color: var(--accent); background: rgba(0,255,179,0.08); padding: 2px 5px; border-radius: 3px; }

/* COPY BAR */
.copy-bar { display: none; margin: 0 12px 12px; padding: 12px 16px; background: var(--s1); border: 1px solid var(--border); border-radius: 10px; align-items: center; justify-content: space-between; gap: 12px; }
.copy-bar.show { display: flex; }
.copy-info { font-size: 10px; color: var(--muted2); letter-spacing: 1px; text-transform: uppercase; line-height: 1.6; }
.copy-btn { all: unset; cursor: pointer; font-family: var(--display); font-weight: 700; font-size: 13px; letter-spacing: 0.5px; color: var(--accent); border: 1px solid rgba(0,255,179,0.25); padding: 8px 14px; border-radius: 7px; white-space: nowrap; min-height: 40px; display: flex; align-items: center; }
.copy-btn:active { background: rgba(0,255,179,0.08); }

/* SKELETON */
.skeleton { background: linear-gradient(90deg, var(--s1) 25%, var(--s2) 50%, var(--s1) 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 6px; }
@keyframes shimmer { to { background-position: -200% 0; } }
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="wordmark">Block<em>Arb</em></div>
    <div class="wordmark-sub">Spread Monitor</div>
  </div>
  <button class="fetch-btn" id="fetchBtn" onclick="fetchSpreads()">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
    </svg>
    Fetch
  </button>
</div>

<div class="status-bar" id="statusBar">
  <span id="statusText">READY</span>
  <span id="timestamp"></span>
</div>

<div class="copy-bar" id="copyBar">
  <div class="copy-info">SNAPSHOT READY<br>FOR GENERATOR</div>
  <button class="copy-btn" id="copyBtn" onclick="copyForGenerator()">⎘ Copy</button>
</div>

<div class="content" id="content">
  <div class="empty">
    <div class="empty-icon">◈</div>
    <div class="empty-title">No Data Yet</div>
    <div class="empty-sub">OKX · Kraken · Coinbase<br>Gate.io · Bitfinex · Huobi · KuCoin</div>
  </div>
</div>

<script>
let lastData = null;

async function fetchSpreads() {
  const btn = document.getElementById('fetchBtn');
  const bar = document.getElementById('statusBar');
  const txt = document.getElementById('statusText');
  const ts  = document.getElementById('timestamp');
  const content = document.getElementById('content');
  const copyBar = document.getElementById('copyBar');

  btn.disabled = true;
  btn.classList.add('loading');
  bar.className = 'status-bar live';
  txt.innerHTML = '<span class="pulse"></span>&nbsp; FETCHING';
  ts.textContent = '';
  copyBar.classList.remove('show');
  content.innerHTML = buildSkeletons();

  try {
    const res = await fetch('/api/spreads');
    const json = await res.json();
    if (json.error) throw new Error(json.error);

    lastData = json;
    content.innerHTML = '';
    json.data.forEach((asset, i) => content.appendChild(buildCard(asset, i)));

    bar.className = 'status-bar live';
    txt.innerHTML = '<span class="pulse"></span>&nbsp; LIVE';
    ts.textContent = json.timestamp;
    copyBar.classList.add('show');
  } catch(e) {
    bar.className = 'status-bar err';
    txt.textContent = '✗ ' + e.message;
    content.innerHTML = `<div class="empty"><div class="empty-icon">⚠</div><div class="empty-title">Failed</div><div class="empty-sub">${e.message}</div></div>`;
  }

  btn.disabled = false;
  btn.classList.remove('loading');
}

function buildCard(asset, idx) {
  const card = document.createElement('div');
  card.className = 'card';
  card.style.animationDelay = (idx * 0.07) + 's';

  const bs = asset.best_spread;
  const bsStr = bs !== null ? `${bs > 0 ? '+' : ''}${bs.toFixed(4)}%` : null;
  const chipClass = bs !== null && bs < 0 ? 'best-chip neg' : 'best-chip';
  const isStable = asset.symbol === 'USDT/USD';
  const dec = isStable ? 6 : 2;

  const bookItems = asset.exchanges.map(ex => `
    <div class="book-item">
      <div class="book-item-name">${ex.name}</div>
      <div class="book-price-row"><span class="price-tag">BID</span><span class="price-val">${ex.bid.toFixed(dec)}</span></div>
      <div class="book-price-row"><span class="price-tag">ASK</span><span class="price-val">${ex.ask.toFixed(dec)}</span></div>
    </div>`).join('');

  const spreadRows = asset.pairs.map(p => {
    const isBest = p.label === asset.best_pair;
    return `
      <div class="spread-row">
        <span class="spread-pair">${p.label}</span>
        <div class="spread-right">
          <span class="spread-val ${p.direction}">${p.spread > 0 ? '+' : ''}${p.spread.toFixed(4)}%</span>
          ${isBest ? '<span class="best-star">BEST</span>' : ''}
        </div>
      </div>`;
  }).join('');

  card.innerHTML = `
    <div class="card-head">
      <span class="asset-name">${asset.symbol}</span>
      ${bsStr ? `<span class="${chipClass}">★ ${bsStr}</span>` : ''}
    </div>
    ${bookItems ? `<div class="book-section"><div class="section-label">Top of Book</div><div class="book-grid">${bookItems}</div></div>` : ''}
    ${spreadRows ? `<div class="spreads-section"><div class="section-label">Cross-Exchange Spreads</div>${spreadRows}</div>` : ''}
  `;
  return card;
}

function buildSkeletons() {
  return ['BTC/USDT','ETH/USDT','USDT/USD'].map((sym, i) => `
    <div class="card" style="animation-delay:${i*0.07}s">
      <div class="card-head" style="background:var(--s2)">
        <span class="asset-name" style="color:var(--muted)">${sym}</span>
      </div>
      <div class="book-section">
        <div class="section-label">Top of Book</div>
        <div class="book-grid">
          ${[1,2,3,4].map(() => `<div class="book-item">
            <div class="skeleton" style="height:10px;width:55%;margin-bottom:8px"></div>
            <div class="skeleton" style="height:10px;width:80%;margin-bottom:4px"></div>
            <div class="skeleton" style="height:10px;width:80%"></div>
          </div>`).join('')}
        </div>
      </div>
      <div class="spreads-section">
        <div class="section-label">Spreads</div>
        ${[1,2,3].map(() => `<div class="spread-row">
          <div class="skeleton" style="height:10px;width:55%"></div>
          <div class="skeleton" style="height:10px;width:18%"></div>
        </div>`).join('')}
      </div>
    </div>`).join('');
}

function copyForGenerator() {
  if (!lastData) return;
  let lines = [`BlockArb Spread Snapshot — ${lastData.timestamp}`, ''];
  lastData.data.forEach(asset => {
    lines.push(`── ${asset.symbol}`);
    asset.exchanges.forEach(ex => {
      lines.push(`  ${ex.name.padEnd(10)} bid=${ex.bid.toFixed(6)}  ask=${ex.ask.toFixed(6)}`);
    });
    asset.pairs.forEach(p => {
      const star = p.label === asset.best_pair ? '  ★ BEST' : '';
      lines.push(`  ${p.label.padEnd(32)} ${p.spread > 0 ? '+' : ''}${p.spread.toFixed(4)}%${star}`);
    });
    lines.push('');
  });
  navigator.clipboard.writeText(lines.join('\\n')).then(() => {
    const btn = document.getElementById('copyBtn');
    btn.textContent = '✓ Copied';
    setTimeout(() => { btn.textContent = '⎘ Copy'; }, 2000);
  });
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/spreads")
def api_spreads():
    try:
        return jsonify(fetch_all_spreads())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  BlockArb Spread Monitor → http://0.0.0.0:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
