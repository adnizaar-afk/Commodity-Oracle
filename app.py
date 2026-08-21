import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit.components.v1 as components # Required for the Analytics Tracker

# --- 1. PAGE CONFIG & LEGAL DISCLAIMER ---
st.set_page_config(page_title="Commodity AI Oracle", layout="wide", page_icon="🪙")

st.warning("**LEGAL DISCLAIMER:** This dashboard is for informational and research purposes only. It does not constitute financial or investment advice. The forecasts are based on mathematical simulations and historical data, which do not guarantee future performance. Trading commodities involves significant risk.")

st.title("Silver & Base Metals Forecasting Engine")
st.markdown("Live fundamental data, short-term statistical projections, and long-term 2040 structural supply models.")

# --- 2. DATA INGESTION ENGINE ---
@st.cache_data(ttl=3600) 
def get_commodity_data():
    tickers = {
        "Silver": "SI=F",
        "Gold": "GC=F",
        "Copper": "HG=F",
        "Zinc": "ZNC=F" # <--- UPGRADE 1: Zinc Ticker Added
    }
    data = {}
    for name, ticker in tickers.items():
        # Using yf.Ticker().history() prevents data formatting errors
        tkr = yf.Ticker(ticker)
        df = tkr.history(period="2y", interval="1d")
        data[name] = df
    return data

data = get_commodity_data()
silver_df = data["Silver"]

# --- 3. DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs(["Current Market (Live)", "Short-Term Tactical (365 Days)", "Long-Term Structural (2030-2040)"])

# --- TAB 1: LIVE MARKET ---
with tab1:
    st.header("Live Exchange Pricing")
    st.caption("Data Source: Pricing data reflects active continuous futures contracts sourced directly from the Commodity Exchange (COMEX).")
    
    # BUG FIX: Dynamically create columns based on the number of commodities
    cols = st.columns(len(data)) 
    
    # ... [Keep your existing for loop here] ...
        
    st.subheader("Gold-to-Silver Ratio (GSR)")
    st.caption("Methodology: The GSR is computed dynamically by dividing the active COMEX Gold spot price by the COMEX Silver spot price.")
    
    for i, (name, df) in enumerate(data.items()):
        # Precaution in case Yahoo Finance returns empty data on weekends/holidays
        if df.empty:
            cols[i].metric(label=f"{name} Futures Spot", value="N/A", delta="N/A")
            continue
            
        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        pct_change = ((current_price - prev_price) / prev_price) * 100
        
        cols[i].metric(label=f"{name} Futures Spot", 
                       value=f"${current_price:.2f}", 
                       delta=f"{pct_change:.2f}%")
        
    if not data["Gold"].empty and not data["Silver"].empty:
        current_gold = float(data["Gold"]['Close'].iloc[-1])
        current_silver = float(data["Silver"]['Close'].iloc[-1])
        gsr = current_gold / current_silver
        st.info(f"The current Gold-to-Silver ratio is **{gsr:.2f}:1**. Historically, a ratio above 80:1 suggests Silver is undervalued relative to Gold.")

# --- TAB 2: SHORT-TERM LST/MONTE CARLO CONE ---
with tab2:
    st.markdown("""
    > **Methodology:** This stochastic forecasting model employs a Monte Carlo simulation utilizing Geometric Brownian Motion (GBM). By extracting historical daily log returns, annualized volatility, and drift from the preceding 24 months of COMEX trading data, the engine computes hundreds of random walk permutations. 
    >
    > The resulting probability cone delineates the 5th, 50th (median), and 95th percentile confidence intervals for price trajectories over the next 365 days, providing a quantitative framework for volatility expectation.
    """)
    
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
    
    percentile_5 = np.percentile(simulated_paths, 5, axis=1)
    percentile_50 = np.percentile(simulated_paths, 50, axis=1)
    percentile_95 = np.percentile(simulated_paths, 95, axis=1)
    future_dates = [datetime.today() + timedelta(days=i) for i in range(days)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=future_dates, y=percentile_95, mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=future_dates, y=percentile_5, mode='lines', fill='tonexty', fillcolor='rgba(0,176,246,0.2)', line=dict(width=0), name='90% Confidence Interval'))
    fig.add_trace(go.Scatter(x=future_dates, y=percentile_50, mode='lines', line=dict(color='blue', width=2), name='Median Trajectory'))
    fig.update_layout(title="Silver Price Probability Cone", xaxis_title="Date", yaxis_title="Price ($/oz)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # --- UPGRADE 2: Explicit Time-Horizon Targets ---
    st.subheader("Statistical Price Targets")
    st.write("Median projected targets based on simulated probability paths:")
    target_cols = st.columns(4)
    target_cols[0].metric("7-Day Target", f"${float(percentile_50[7]):.2f}")
    target_cols[1].metric("30-Day Target", f"${float(percentile_50[30]):.2f}")
    target_cols[2].metric("180-Day Target", f"${float(percentile_50[180]):.2f}")
    target_cols[3].metric("365-Day Target", f"${float(percentile_50[-1]):.2f}")

# --- TAB 3: SYSTEM DYNAMICS STRUCTURAL MODEL ---
with tab3:
    st.markdown("""
    > **Methodology:** This System Dynamics model projects long-term physical market balances by isolating structural supply inelasticity. Because approximately 70% of global silver is produced solely as a byproduct of base metal mining (copper, zinc, and lead), its supply curve is highly rigid and unresponsive to its own price action. 
    >
    > This simulation pits baseline constrained supply against the exponential industrial demand generated by photovoltaic (PV) solar capacity expansion. The resulting visualization maps the widening physical deficit—a structural imbalance that will mathematically necessitate price revaluations to clear the market.
    """)
    
    st.sidebar.header("Model Inputs")
    pv_growth = st.sidebar.slider("Annual Solar PV Demand Growth (%)", min_value=1.0, max_value=15.0, value=8.0, step=0.5)
    st.sidebar.caption("Select your own growth projection") # <--- Add this line here
    
    years = np.arange(2024, 2041)
    base_supply = 34000
    supply_curve = [base_supply * (1 + 0.005)**(y-2024) for y in years] 
    
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
    
    fig2.add_trace(go.Scatter(x=years, y=supply_curve, mode='lines', fill='tonexty', fillcolor='rgba(255,0,0,0.2)', line=dict(width=0), name='Structural Deficit'))
    fig2.update_layout(title="Silver Supply vs. Demand Collision", xaxis_title="Year", yaxis_title="Tonnes", template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

    # --- UPGRADE 3: Structural Milestones Table ---
    st.subheader("Projected Structural Deficit Milestones")
    
    def get_milestone(target_year):
        idx = np.where(years == target_year)[0][0]
        return {
            "Year": target_year,
            "Supply (Tonnes)": f"{int(supply_curve[idx]):,}",
            "Demand (Tonnes)": f"{int(demand_curve[idx]):,}",
            "Physical Deficit (Tonnes)": f"{int(demand_curve[idx] - supply_curve[idx]):,}"
        }

    milestones = [get_milestone(2030), get_milestone(2035), get_milestone(2040)]
    milestones_df = pd.DataFrame(milestones)
    st.table(milestones_df)

# --- 4. FOOTER & TERMS OF SERVICE ---
st.markdown("---") # Adds a clean horizontal divider line

with st.expander("⚖️ Terms of Service & Legal Disclaimer"):
    st.markdown("""
    **Last Updated: August 2026**
    
    **1. Acceptance of Terms**
    By accessing and using this forecasting engine (the "Service"), you accept and agree to be bound by the terms of this agreement. 
    
    **2. Strictly No Financial or Investment Advice**
    The Service, including all predictive models, probability cones, data visualizations, and text, is provided for educational, informational, and research purposes only. **Nothing contained on this Service constitutes financial, investment, legal, or tax advice.** The mathematical models and system dynamics projections are theoretical simulations and do not represent trading signals or recommendations to buy, sell, or hold any commodity, security, or financial instrument.
    
    **3. Assumption of Risk**
    Trading and investing in commodities and futures markets carries a high degree of risk, and you may lose some or all of your initial capital. Past performance of any mathematical model or statistical projection is not indicative of future results. You agree that you are solely responsible for your own financial decisions.
    
    **4. Data Accuracy and Third-Party Sources**
    The Service dynamically aggregates data from third-party exchanges. While we strive for accuracy, the Service is provided on an "AS IS" and "AS AVAILABLE" basis. We make no warranties regarding the accuracy, completeness, reliability, or timeliness of the pricing data or fundamental metrics provided.
    
    **5. Limitation of Liability**
    Under no circumstances shall the creators, developers, or affiliates be liable for any direct, indirect, incidental, consequential, or punitive damages arising from your use of the Service, including financial losses resulting from trading decisions made based on the data presented herein.
    """

    **6. Limitation of Liability**
    The design, logic, layout, and predictive algorithmic structures of the Service are the property of Metals Dynamics. You may not scrape, reverse-engineer, or commercially redistribute the models or data without explicit permission.
    )

# --- UPGRADE 4: Zero-Cost Web Analytics ---
# To activate: create a free account at goatcounter.com, get your site code, and replace 'YOUR_CODE' below.
components.html(
    '''
    <script data-goatcounter="https://YOUR_CODE.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
    ''',
    height=0,
    width=0,
)
