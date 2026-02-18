"""Streamlit Dashboard for DRL vs Scanner Comparison

Interactive dashboard to visualize parallel testing results.
Compare performance, agreement rates, and signal quality.

Usage:
    streamlit run drl_comparison_dashboard.py
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page config
st.set_page_config(page_title="DRL vs Scanner Comparison", layout="wide", page_icon="🤖")

st.title("🤖 DRL vs Scanner - Parallel Testing Dashboard")

# Sidebar
st.sidebar.header("⚙️ Settings")

log_dir = Path(st.sidebar.text_input("Log Directory", "logs/parallel_testing"))

# Load available sessions
if log_dir.exists():
    csv_files = sorted(log_dir.glob("*_signals.csv"), reverse=True)
    json_files = sorted(log_dir.glob("*_metadata.json"), reverse=True)

    if csv_files:
        selected_session = st.sidebar.selectbox(
            "Select Session",
            options=[f.stem.replace("_signals", "") for f in csv_files],
            format_func=lambda x: f"Session: {x}",
        )

        # Load data
        csv_path = log_dir / f"{selected_session}_signals.csv"
        json_path = log_dir / f"{selected_session}_metadata.json"

        if csv_path.exists():
            df = pd.read_csv(csv_path)

            # Load metadata
            metadata = {}
            if json_path.exists():
                with open(json_path) as f:
                    metadata = json.load(f)

            # Display metadata
            st.sidebar.markdown("---")
            st.sidebar.subheader("📊 Session Info")
            st.sidebar.write(f"**Mode:** {metadata.get('strategy_mode', 'N/A')}")
            st.sidebar.write(f"**Total Signals:** {metadata.get('total_signals', 0)}")
            st.sidebar.write(f"**Agreement Rate:** {metadata.get('agreement_rate', 0):.1%}")
            st.sidebar.write(f"**Avg Confidence:** {metadata.get('avg_confidence', 0):.1%}")

            # Main dashboard
            tab1, tab2, tab3, tab4 = st.tabs(
                ["📊 Overview", "🔍 Signal Analysis", "📈 Performance", "🆚 Comparison"]
            )

            # Tab 1: Overview
            with tab1:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Signals", len(df))

                with col2:
                    buy_count = len(df[df["final_action"] == "BUY"])
                    st.metric("BUY Signals", buy_count, delta=f"{buy_count/len(df)*100:.1f}%")

                with col3:
                    agreement_rate = df["agreement"].mean()
                    st.metric("Agreement Rate", f"{agreement_rate:.1%}")

                with col4:
                    avg_conf = df["final_confidence"].mean()
                    st.metric("Avg Confidence", f"{avg_conf:.1%}")

                # Action distribution
                st.subheader("📊 Action Distribution")
                action_counts = df["final_action"].value_counts()
                fig_actions = px.pie(
                    values=action_counts.values,
                    names=action_counts.index,
                    title="Final Action Distribution",
                    color_discrete_map={"BUY": "green", "SELL": "red", "HOLD": "gray"},
                )
                st.plotly_chart(fig_actions, use_container_width=True)

                # Agreement analysis
                st.subheader("🤝 Scanner-DRL Agreement")
                col1, col2 = st.columns(2)

                with col1:
                    agreement_counts = df["agreement"].value_counts()
                    fig_agreement = px.bar(
                        x=["Agree", "Disagree"],
                        y=[
                            agreement_counts.get(True, 0),
                            agreement_counts.get(False, 0),
                        ],
                        title="Agreement Distribution",
                        labels={"x": "Status", "y": "Count"},
                        color=["Agree", "Disagree"],
                        color_discrete_map={"Agree": "green", "Disagree": "orange"},
                    )
                    st.plotly_chart(fig_agreement, use_container_width=True)

                with col2:
                    # Confidence by agreement
                    fig_conf = px.box(
                        df,
                        x="agreement",
                        y="final_confidence",
                        title="Confidence Distribution by Agreement",
                        labels={"agreement": "Agreement", "final_confidence": "Confidence"},
                        color="agreement",
                    )
                    st.plotly_chart(fig_conf, use_container_width=True)

            # Tab 2: Signal Analysis
            with tab2:
                st.subheader("🔍 Detailed Signal Breakdown")

                # Filter options
                col1, col2, col3 = st.columns(3)
                with col1:
                    action_filter = st.multiselect(
                        "Filter by Action",
                        options=df["final_action"].unique(),
                        default=df["final_action"].unique(),
                    )

                with col2:
                    agreement_filter = st.selectbox("Agreement", ["All", "Agree", "Disagree"])

                with col3:
                    min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.0)

                # Apply filters
                filtered_df = df[df["final_action"].isin(action_filter)]
                if agreement_filter == "Agree":
                    filtered_df = filtered_df[filtered_df["agreement"] == True]
                elif agreement_filter == "Disagree":
                    filtered_df = filtered_df[filtered_df["agreement"] == False]
                filtered_df = filtered_df[filtered_df["final_confidence"] >= min_confidence]

                # Display table
                st.dataframe(
                    filtered_df[
                        [
                            "symbol",
                            "scanner_action",
                            "scanner_score",
                            "drl_action",
                            "drl_confidence",
                            "final_action",
                            "final_confidence",
                            "agreement",
                            "risk_adjusted_size",
                        ]
                    ].style.background_gradient(subset=["final_confidence"], cmap="RdYlGn"),
                    use_container_width=True,
                )

                # Position sizing analysis
                st.subheader("💰 Position Sizing Distribution")
                fig_pos = px.histogram(
                    filtered_df,
                    x="risk_adjusted_size",
                    nbins=20,
                    title="Risk-Adjusted Position Size Distribution",
                    labels={"risk_adjusted_size": "Position Size"},
                )
                st.plotly_chart(fig_pos, use_container_width=True)

            # Tab 3: Performance
            with tab3:
                st.subheader("📈 Performance Metrics")
                st.info("⚠️ Performance tracking requires paper trading or backtest data")

                # Placeholder for future performance metrics
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Scanner Win Rate", "N/A", help="Requires historical execution data")
                    st.metric("DRL Win Rate", "N/A", help="Requires historical execution data")

                with col2:
                    st.metric("Scanner Avg Return", "N/A", help="Requires historical execution data")
                    st.metric("DRL Avg Return", "N/A", help="Requires historical execution data")

                st.markdown(
                    """
                **To enable performance tracking:**
                1. Run paper trading with both strategies
                2. Log execution results to database
                3. Calculate returns for each signal type
                4. Update this dashboard with actual performance data
                """
                )

            # Tab 4: Comparison
            with tab4:
                st.subheader("🆚 Scanner vs DRL Comparison")

                # Action agreement matrix
                st.subheader("Action Agreement Matrix")

                if "scanner_action" in df.columns and "drl_action" in df.columns:
                    # Create confusion matrix
                    matrix_data = []
                    for scanner_action in ["BUY", "SELL", "HOLD"]:
                        row = []
                        for drl_action in ["BUY", "SELL", "HOLD"]:
                            count = len(
                                df[
                                    (df["scanner_action"] == scanner_action)
                                    & (df["drl_action"] == drl_action)
                                ]
                            )
                            row.append(count)
                        matrix_data.append(row)

                    fig_matrix = go.Figure(
                        data=go.Heatmap(
                            z=matrix_data,
                            x=["BUY", "SELL", "HOLD"],
                            y=["BUY", "SELL", "HOLD"],
                            colorscale="Blues",
                            text=matrix_data,
                            texttemplate="%{text}",
                        )
                    )
                    fig_matrix.update_layout(
                        title="Scanner (Y) vs DRL (X) Action Agreement",
                        xaxis_title="DRL Action",
                        yaxis_title="Scanner Action",
                    )
                    st.plotly_chart(fig_matrix, use_container_width=True)

                # Confidence comparison
                st.subheader("Confidence Levels Comparison")
                col1, col2 = st.columns(2)

                with col1:
                    fig_scanner_conf = px.histogram(
                        df,
                        x="scanner_score",
                        title="Scanner Signal Strength",
                        labels={"scanner_score": "Score"},
                    )
                    st.plotly_chart(fig_scanner_conf, use_container_width=True)

                with col2:
                    if "drl_confidence" in df.columns:
                        fig_drl_conf = px.histogram(
                            df.dropna(subset=["drl_confidence"]),
                            x="drl_confidence",
                            title="DRL Confidence Distribution",
                            labels={"drl_confidence": "Confidence"},
                        )
                        st.plotly_chart(fig_drl_conf, use_container_width=True)

        else:
            st.error(f"Session data not found: {csv_path}")
    else:
        st.warning(f"No session data found in {log_dir}")
else:
    st.error(f"Log directory not found: {log_dir}")

# Footer
st.markdown("---")
st.markdown("🤖 **FinPilot DRL Parallel Testing Dashboard** | Real-time AI vs Rule-based Comparison")
