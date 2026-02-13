import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import time

# ==========================================================
# 1. CORE ANALYTICS & DATA RECOVERY ENGINE
# ==========================================================

class QuantEngine:
    """Handles high-fidelity data extraction with built-in recovery for 2026 data formats."""
    
    @staticmethod
    @st.cache_data(ttl=300)
    def fetch_market_data(symbol, interval, retries=3):
        """Fetches data with retry logic and forced column flattening to prevent blank charts."""
        symbol = symbol.strip().upper()
        if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
            symbol += ".NS"

        # Safe historical window mapping for 2026 yfinance constraints
        period_map = {"5m": "5d", "15m": "7d", "1h": "60d", "1d": "max"}
        period = period_map.get(interval, "1mo")

        for attempt in range(retries):
            try:
                # auto_adjust=True is critical for clean OHLC data
                df = yf.download(symbol, interval=interval, period=period, progress=False, auto_adjust=True)
                
                if not df.empty:
                    # --- THE 2026 DATA FIX: FLATTEN MULTI-INDEX ---
                    # Prevents "Terminal Connection Failure" caused by nested headers
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    df.index = pd.to_datetime(df.index)
                    return df, symbol
                
                time.sleep(1) # Interval pause for network stability
            except Exception as e:
                if attempt == retries - 1:
                    return None, symbol
        return None, symbol

    @staticmethod
    def calculate_audit_technicals(df):
        """Vectorized technical library for professional auditing."""
        # 1. RSI (14 Period) - Momentum
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 2. Institutional Moving Averages
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # 3. VWAP (Volume Weighted Average Price)
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()

        # 4. Yearly Benchmarks
        df['52W_High'] = df['High'].rolling(window=252, min_periods=1).max()
        df['52W_Low'] = df['Low'].rolling(window=252, min_periods=1).min()
        df['20D_Avg_Vol'] = df['Volume'].rolling(window=20).mean()
        
        # 5. Volatility Analysis
        df['Day_Chg_Pct'] = df['Close'].pct_change() * 100

        return df

# ==========================================================
# 2. TERMINAL USER INTERFACE (DARK MODE)
# ==========================================================

st.set_page_config(page_title="Quant Terminal Pro v3.0", layout="wide")

# CSS for Dark Professional Aesthetic (Matching #131722)
st.markdown("""
    <style>
    .main { background-color: #131722; color: #d1d4dc; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363c4e; border-radius: 10px; padding: 15px; }
    [data-testid="stMetricValue"] { color: #2962ff !important; font-family: 'Courier New', monospace; font-weight: bold; }
    .stSidebar { background-color: #131722 !important; border-right: 1px solid #363c4e; }
    .stDataFrame { background-color: #1e222d; border-radius: 8px; }
    h1, h2, h3 { color: #ffffff; }
    hr { border: 1px solid #363c4e; }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR: Terminal Controls
st.sidebar.title("💎 Quant Terminal")
st.sidebar.caption("v3.0 Institutional Master")
ticker_input = st.sidebar.text_input("Enter NSE Ticker:", "RELIANCE").upper()
interval_input = st.sidebar.selectbox("Analysis Interval:", ["5m", "15m", "1h", "1d"], index=1)

# EXECUTION FLOW
engine = QuantEngine()
raw_data, full_symbol = engine.fetch_market_data(ticker_input, interval_input)

if raw_data is not None:
    # Generate Technicals
    df = engine.calculate_audit_technicals(raw_data)
    last_tick = df.iloc[-1]
    
    # --- HEADER SECTION ---
    st.title(f"📊 {full_symbol} Intelligence Report")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("LTP (Price)", f"₹{last_tick['Close']:,.2f}", f"{last_tick['Day_Chg_Pct']:.2f}%")
    kpi2.metric("RSI (14)", f"{last_tick['RSI']:.2f}")
    kpi3.metric("VWAP", f"₹{last_tick['VWAP']:,.2f}")
    
    # RSI Based Signal Logic
    rsi_val = last_tick['RSI']
    action, signal_col = ("BUY", "green") if rsi_val < 35 else ("SELL", "red") if rsi_val > 65 else ("HOLD", "gray")
    kpi4.markdown(f"**Terminal Signal:**\n### :{signal_col}[{action}]")

    st.markdown("---")

    # --- TECHNICAL SCORECARD (TABULAR GRID) ---
    st.subheader("📋 Fundamental & Technical Scorecard")
    
    
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    
    with t_col1:
        st.write("**Session Data**")
        st.write(f"Open: **{last_tick['Open']:,.2f}**")
        st.write(f"High: **{last_tick['High']:,.2f}**")
        st.write(f"Low: **{last_tick['Low']:,.2f}**")
        st.write(f"Prev Close: **{df['Close'].iloc[-2]:,.2f}**")

    with t_col2:
        st.write("**Institutional Levels**")
        st.write(f"VWAP: **{last_tick['VWAP']:,.2f}**")
        st.write(f"EMA 20: **{last_tick['EMA_20']:,.2f}**")
        st.write(f"SMA 50: **{last_tick['SMA_50']:,.2f}**")
        st.write(f"SMA 200: **{last_tick['SMA_200']:,.2f}**")

    with t_col3:
        st.write("**Yearly Range**")
        st.write(f"52W High: **{last_tick['52W_High']:,.2f}**")
        st.write(f"52W Low: **{last_tick['52W_Low']:,.2f}**")
        st.write(f"20D Avg Vol: **{int(last_tick['20D_Avg_Vol']):,}**")
        st.write(f"Volume: **{int(last_tick['Volume']):,}**")

    with t_col4:
        st.write("**Momentum Stats**")
        st.write(f"RSI Value: **{last_tick['RSI']:.2f}**")
        st.write(f"Day Change: **{last_tick['Day_Chg_Pct']:.2f}%**")
        zone = "Oversold" if rsi_val < 30 else "Overbought" if rsi_val > 70 else "Neutral"
        st.write(f"Zone: **{zone}**")

    st.markdown("---")

    # --- RSI MOMENTUM VISUALIZER ---
    st.subheader("📈 Momentum Oscillator (RSI)")
    
    
    rsi_fig = go.Figure()
    
    # RSI Trace
    rsi_fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'],
        line=dict(color='#2962ff', width=2.5),
        fill='toself', fillcolor='rgba(41, 98, 255, 0.05)',
        name="RSI 14"
    ))
    
    # Threshold Lines
    rsi_fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", annotation_text="Overbought")
    rsi_fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", annotation_text="Oversold")
    
    rsi_fig.update_layout(
        height=450,
        template="plotly_dark",
        plot_bgcolor='#131722',
        paper_bgcolor='#131722',
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(gridcolor='#1e222d', rangeslider_visible=True, showgrid=True), # Scrollable
        yaxis=dict(gridcolor='#1e222d', range=[0, 100], side="right", showgrid=True),
        hovermode="x unified"
    )
    
    st.plotly_chart(rsi_fig, use_container_width=True)

    # --- HISTORICAL AUDIT TABLE ---
    with st.expander("📝 View Full Institutional Audit Table"):
        display_df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'VWAP', 'EMA_20']].sort_index(ascending=False).head(100)
        st.dataframe(display_df.style.format("{:,.2f}"), use_container_width=True)

else:
    st.error("⚠️ Terminal Connection Failure: Ensure the ticker is valid (e.g. TCS, IRFC) or check internet connection.")
    st.info("Tip: Try searching for RELIANCE or ZOMATO to test connection.")
