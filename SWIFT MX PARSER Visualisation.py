import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt
import pandas as pd
import math

session = get_active_session()

df = session.sql("""
    SELECT DISTINCT debtor_name, creditor_name, SUM(amount) as amount
    FROM parsed_mx_messages 
    WHERE debtor_name IS NOT NULL
    GROUP BY debtor_name, creditor_name
""").to_pandas()

st.title("Debtor → Creditor Network")

if df.empty:
    st.warning("No data found")
    st.stop()

nodes = list(set(df['DEBTOR_NAME'].tolist() + df['CREDITOR_NAME'].tolist()))
n = len(nodes)
debtors = set(df['DEBTOR_NAME'])

node_df = pd.DataFrame({
    'name': nodes,
    'x': [math.cos(2 * math.pi * i / n) * 200 + 300 for i in range(n)],
    'y': [math.sin(2 * math.pi * i / n) * 200 + 250 for i in range(n)],
    'type': ['Debtor' if name in debtors else 'Creditor' for name in nodes]
})

pos = {row['name']: (row['x'], row['y']) for _, row in node_df.iterrows()}
edge_df = pd.DataFrame({
    'x': [pos[r['DEBTOR_NAME']][0] for _, r in df.iterrows()],
    'y': [pos[r['DEBTOR_NAME']][1] for _, r in df.iterrows()],
    'x2': [pos[r['CREDITOR_NAME']][0] for _, r in df.iterrows()],
    'y2': [pos[r['CREDITOR_NAME']][1] for _, r in df.iterrows()],
    'mid_x': [(pos[r['DEBTOR_NAME']][0] + pos[r['CREDITOR_NAME']][0]) / 2 for _, r in df.iterrows()],
    'mid_y': [(pos[r['DEBTOR_NAME']][1] + pos[r['CREDITOR_NAME']][1]) / 2 for _, r in df.iterrows()],
    'amount': df['AMOUNT'].tolist(),
    'label': ['$' + f"{a:,.0f}" for a in df['AMOUNT']],
    'debtor': df['DEBTOR_NAME'].tolist(),
    'creditor': df['CREDITOR_NAME'].tolist()
})

edges = alt.Chart(edge_df).mark_rule(strokeWidth=2, opacity=0.6, color='#888').encode(
    x=alt.X('x:Q', scale=alt.Scale(domain=[0, 600]), axis=None),
    y=alt.Y('y:Q', scale=alt.Scale(domain=[0, 500]), axis=None),
    x2='x2:Q', y2='y2:Q',
    tooltip=['debtor:N', 'creditor:N', 'amount:Q']
)

edge_labels = alt.Chart(edge_df).mark_text(fontSize=11, fontWeight='bold').encode(
    x='mid_x:Q', y='mid_y:Q', text='label:N'
)

nodes_chart = alt.Chart(node_df).mark_circle(size=800).encode(
    x='x:Q', y='y:Q',
    color=alt.Color('type:N', scale=alt.Scale(domain=['Debtor', 'Creditor'], range=['#ff6b6b', '#4ecdc4'])),
    tooltip=['name:N', 'type:N']
)

labels = alt.Chart(node_df).mark_text(dy=-25, fontSize=12, fontWeight='bold').encode(
    x='x:Q', y='y:Q', text='name:N'
)

chart = (edges + edge_labels + nodes_chart + labels).properties(width=600, height=500).configure_view(strokeWidth=0)
st.altair_chart(chart, use_container_width=True)

st.caption("🔴 Debtor  |  🟢 Creditor  |  Hover for details (dragging not supported in Snowflake)")