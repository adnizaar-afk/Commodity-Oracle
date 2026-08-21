import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & LEGAL DISCLAIMER ---
st.set_page_config(page_title="Commodity AI Oracle", layout="wide", page_icon="🪙")

st.warning("**LEGAL DISCLAIMER:** This dashboard is for informational and research purposes only. It does not constitute financial or investment advice. The forecasts are based on mathematical simulations and historical data, which do not guarantee future performance. Trading commodities involves significant risk.")

st.title("Silver & Base Metals Forecasting Engine")
st.markdown("Live fundamental data, short-term statistical projections, and long-term 2040 structural supply models.")

# --- 2. DATA INGESTION ENGINE ---
@st.cache_data(ttl=3600) # Caches the data for 1 hour to prevent hitting API limits
def get_commodity_data():
    tickers = {
        "Silver": "SI=F",
        "Gold": "GC=F",
        "Copper": "HG=F"
    }
    data = {}
    for name, ticker in tickers.items():
        # Fetch the last 2 years of data for the baseline
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
        data[name] = df
    return data

data = get_commodity_data()
silver_df = data["Silver"]

# --- 3. DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs(["Current Market (Live)", "Short-Term Tactical (365 Days)", "Long-Term Structural (2030-2040)"])

# --- TAB 1: LIVE MARKET ---
with tab1:
    st.header("Live Exchange Pricing")
    cols = st.columns(3)
    
    for i, (name, df) in enumerate(data.items()):
        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        pct_change = ((current_price - prev_price) / prev_price) * 100
        
        cols[i].metric(label=f"{name} Futures Spot", 
                       value=f"${current_price:.2f}", 
                       delta=f"{pct_change:.2f}%")
        
    st.subheader("Gold-to-Silver Ratio (GSR)")
    current_gold = float(data["Gold"]['Close'].iloc[-1])
    current_silver = float(data["Silver"]['Close'].iloc[-1])
    gsr = current_gold / current_silver
    st.info(f"The current Gold-to-Silver ratio is **{gsr:.2f}:1**. Historically, a ratio above 80:1 suggests Silver is undervalued relative to Gold.")

# --- TAB 2: SHORT-TERM LST/MONTE CARLO CONE ---
with tab2:
    st.header("365-Day Probability Cone (Monte Carlo Simulation)")
    st.write("This model calculates a probability cone based on historical volatility and drift over the last 24 months.")
    
    # Mathematical Simulation Logic
    returns = silver_df['Close'].pct_change().dropna()
    mu = returns.mean()
    sigma = returns.std()
    last_price = float(silver_df['Close'].iloc[-1])
    
    days = 365
    simulations = 100
    simulated_paths = np.zeros((days, simulations))
    simulated_paths[0] = last_price
    
    for t in range(1, days):
        random_shocks = np.random.normal(loc=mu, scale=sigma, size=simulations)
        simulated_paths[t] = simulated_paths[t-1] * (1 + random_shocks)
    
    # Calculate percentiles for the cone
    percentile_5 = np.percentile(simulated_paths, 5, axis=1)
    percentile_50 = np.percentile(simulated_paths, 50, axis=1)
    percentile_95 = np.percentile(simulated_paths, 95, axis=1)
    future_dates = [datetime.today() + timedelta(days=i) for i in range(days)]
    
    # Plotting the cone
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=future_dates, y=percentile_95, mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=future_dates, y=percentile_5, mode='lines', fill='tonexty', fillcolor='rgba(0,176,246,0.2)', line=dict(width=0), name='90% Confidence Interval'))
    fig.add_trace(go.Scatter(x=future_dates, y=percentile_50, mode='lines', line=dict(color='blue', width=2), name='Median Trajectory'))
    fig.update_layout(title="Silver Price Probability Cone", xaxis_title="Date", yaxis_title="Price ($/oz)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: SYSTEM DYNAMICS STRUCTURAL MODEL ---
with tab3:
    st.header("System Dynamics: The 2040 Supply Deficit")
    st.markdown("Because 70% of silver is a byproduct of zinc and copper mining, supply is inelastic. This model projects the deficit caused by the exponential growth of solar photovoltaics (PV).")
    
    st.sidebar.header("Model Inputs")
    pv_growth = st.sidebar.slider("Annual Solar PV Demand Growth (%)", min_value=1.0, max_value=15.0, value=8.0, step=0.5)
    
    # Synthetic long-term model generation
    years = np.arange(2024, 2041)
    base_supply = 34000 # tonnes
    supply_curve = [base_supply * (1 + 0.005)**(y-2024) for y in years] # Minimal 0.5% growth
    
    base_pv_demand = 6000
    base_industrial_demand = 18000
    demand_curve = []
    
    for y in years:
        pv = base_pv_demand * (1 + (pv_growth/100))**(y-2024)
        total_demand = pv + base_industrial_demand
        demand_curve.append(total_demand)
        
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=years, y=supply_curve, mode='lines', line=dict(color='red', width=3), name='Inelastic Mine Supply'))
    fig2.add_trace(go.Scatter(x=years, y=demand_curve, mode='lines', line=dict(color='green', width=3), name='Total Industrial Demand (Driven by PV)'))
    
    # Shade the deficit
    fig2.add_trace(go.Scatter(x=years, y=supply_curve, mode='lines', fill='tonexty', fillcolor='rgba(255,0,0,0.2)', line=dict(width=0), name='Structural Deficit'))
    fig2.update_layout(title="Silver Supply vs. Demand Collision", xaxis_title="Year", yaxis_title="Tonnes", template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)
    
    st.info("As the red shaded area (the deficit) grows, above-ground warehouse inventories will be depleted, mathematically forcing the price of physical metal upward to destroy demand.")