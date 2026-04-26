import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# Create a title
st.title("My First Streamlit App")

# Create a dataframe
df = pd.DataFrame({
    'column_1': [1, 2, 3, 4],
    'column_2': [10, 20, 30, 40]
})

st.write(df)