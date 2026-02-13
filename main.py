import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ==========================================================
# 1. SMART SEARCH & DATA ENGINE
# ==========================================================

class SmartQuantEngine:
    """Handles smart ticker searching and technical auditing."""
    
    @staticmethod
    @st.cache_data(ttl=60)
    def fetch_data(user_input, interval):
        """
        Smart Search: Automatically adds .NS for Indian stocks if the user 
        forgets, making it beginner-friendly.
        """
        try:
            query = user_input.strip().upper()
            
            # --- BEGINNER FRIENDLY LOGIC ---
            # If it's a standard name like 'RELIANCE', we try adding .NS (NSE) 
            # so the beginner doesn't have to know technical suffixes.
            possible_tickers = [query]
            if "." not in query:
                possible_tickers.insert(0, f"{query}.NS")
            
            df = pd.DataFrame()
            final_symbol = query
            
            for ticker in possible_tickers:
                # Dynamic period mapping for 2026 data stability
                period = "60d" if interval in ["15m", "1h"] else "max"
                df = yf.download(ticker, interval=interval, period=period, progress=False, auto_adjust=True)
                if not df.empty:
                    final_symbol = ticker
                    break
            
            if df.empty:
                return None, query

            # --- 2026 DATA FIX: FLATTEN MULTI-INDEX HEADERS ---
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df.index = pd.to_datetime(df.index)
            return df, final_symbol
        except Exception:
            return None, user_input

    @staticmethod
    def apply_technicals(df):
        # RSI 14 (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))

        # VWAP (Volume Weighted Average Price)
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()

        # Institutional Moving Averages
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # High/Low Benchmarks
        df['52W_H'] = df['High'].rolling(window=252, min_periods=1).max()
        df['52W_L'] = df['Low'].rolling(window=252, min_periods=1).min()
        
        return df

# ==========================================================
# 2. UI ARCHITECTURE & STATE MANAGEMENT
# ==========================================================

st.set_page_config(page_title="QuantPro Terminal", layout="wide", page_icon="💎")

# Initialize App Memory
if 'app_state' not in st.session_state:
    st.session_state.app_state = "welcome" 
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["RELIANCE", "ZOMATO", "TCS", "IRFC"]
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = "RELIANCE"

# Professional Theme Injection
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    .stSidebar { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    .welcome-card { text-align: center; padding: 80px 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 3. SIDEBAR: NAVIGATION & WATCHLIST
# ==========================================================

st.sidebar.title("💎 QuantPro")
st.sidebar.caption("v3.0 Institutional Edition")

if st.sidebar.button("🏠 Home / Welcome Screen", use_container_width=True):
    st.session_state.app_state = "welcome"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Your Watchlist")
for item in st.session_state.watchlist:
    cols = st.sidebar.columns([4, 1])
    if cols[0].button(f"📊 {item}", key=f"nav_{item}", use_container_width=True):
        st.session_state.active_ticker = item
        st.session_state.app_state = "terminal"
        st.rerun()
    if cols[1].button("✖", key=f"del_{item}"):
        st.session_state.watchlist.remove(item)
        st.rerun()

st.sidebar.markdown("---")
# BEGINNER FRIENDLY SEARCH
search_q = st.sidebar.text_input("🔍 Search Any Stock", placeholder="e.g. INFOSYS").upper()
if st.sidebar.button("Launch Analysis", use_container_width=True):
    if search_q:
        if search_q not in st.session_state.watchlist:
            st.session_state.watchlist.append(search_q)
        st.session_state.active_ticker = search_q
        st.session_state.app_state = "terminal"
        st.rerun()

# ==========================================================
# 4. PAGE ROUTING
# ==========================================================

if st.session_state.app_state == "welcome":
    # --- WELCOME / SPLASH SCREEN ---
    st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
    st.title("Welcome to QuantPro")
    st.subheader("Professional Grade Market Auditing for Everyone")
    
    
    
    st.write("Analyze momentum, institutional VWAP, and key technical levels with one click.")
    
    c1, c2, c3 = st.columns([2, 1, 2])
    if c2.button("🚀 Open Terminal", use_container_width=True):
        st.session_state.app_state = "terminal"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    f1, f2, f3 = st.columns(3)
    f1.info("💡 **Smart Search**\n\nJust type the name. We handle the technical suffixes automatically.")
    f2.success("📈 **Momentum Tools**\n\nDeep RSI analysis with full historical scroll control.")
    f3.warning("📋 **Quick Watchlist**\n\nSave your favorite assets and switch between them instantly.")

elif st.session_state.app_state == "terminal":
    # --- TERMINAL / DASHBOARD PAGE ---
    engine = SmartQuantEngine()
    interval = st.sidebar.selectbox("⏱️ Timeframe", ["15m", "1h", "1d"], index=0)
    
    data, ticker_identity = engine.fetch_data(st.session_state.active_ticker, interval)

    if data is not None:
        df = engine.apply_technicals(data)
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Header Row
        h1, h2 = st.columns([3, 1])
        h1.title(f"📊 {ticker_identity}")
        
        change_val = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        h2.metric("LTP", f"₹{last['Close']:,.2f}", f"{change_val:.2f}%")

        # TECHNICAL SCORECARD (GRID VIEW)
        st.subheader("📋 Technical Scorecard")
        
        
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.write("**Session**")
            st.write(f"Open: **{last['Open']:,.2f}**")
            st.write(f"High: **{last['High']:,.2f}**")
            st.write(f"Low: **{last['Low']:,.2f}**")
        with s2:
            st.write("**Institutional**")
            st.write(f"VWAP: **{last['VWAP']:,.2f}**")
            st.write(f"EMA 20: **{last['EMA_20']:,.2f}**")
            st.write(f"SMA 50: **{last['SMA_50']:,.2f}**")
        with s3:
            st.write("**Benchmarks**")
            st.write(f"52W H: **{last['52W_H']:,.2f}**")
            st.write(f"52W L: **{last['52W_L']:,.2f}**")
            st.write(f"Vol: **{int(last['Volume']):,}**")
        with s4:
            st.write("**Momentum**")
            st.write(f"RSI (14): **{last['RSI']:.2f}**")
            rsi_val = last['RSI']
            zone = "OVERSOLD" if rsi_val < 30 else "OVERBOUGHT" if rsi_val > 70 else "NEUTRAL"
            st.write(f"Zone: **{zone}**")

        st.markdown("---")

        # TABS: CHART & AUDIT
        tab_chart, tab_audit = st.tabs(["📉 RSI Momentum Visualizer", "📝 Historical Audit Logs"])

        with tab_chart:
            st.subheader("Relative Strength Index (RSI)")
            
            # --- THE SCROLLABLE CHART ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index, y=df['RSI'],
                line=dict(color='#58a6ff', width=2),
                fill='toself', fillcolor='rgba(88, 166, 255, 0.05)',
                name="RSI"
            ))
            
            fig.add_hline(y=70, line_dash="dash", line_color="#f85149", annotation_text="Overbought")
            fig.add_hline(y=30, line_dash="dash", line_color="#3fb950", annotation_text="Oversold")
            
            fig.update_layout(
                height=500, template="plotly_dark",
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#30363d', rangeslider_visible=True, showgrid=True), # SCROLL ENABLED
                yaxis=dict(gridcolor='#30363d', side="right", range=[0, 100]),
                margin=dict(l=0, r=50, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_audit:
            st.subheader("Historical Quantitative Logs")
            st.dataframe(df.sort_index(ascending=False).head(200), use_container_width=True)

    else:
        st.error(f"Could not find data for '{st.session_state.active_ticker}'.")
        st.info("Tip: Try searching for common names like RELIANCE, TCS, or HDFC.")

st.sidebar.markdown("---")
st.sidebar.caption("QuantPro Terminal v3.0 | Secure Build 2026")
