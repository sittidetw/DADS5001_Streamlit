import streamlit as st
from streamlit_gsheets import GSheetsConnection
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Note: Providing both `worksheet` and `gid` is redundant.
    # The library prioritizes `worksheet`. I've removed `gid` for clarity.
    # If you intend to select by GID, remove `worksheet` and use `gid` instead.
    # df = conn.read(spreadsheet="1OF9Et2yWFhMfhyNU57iltWGEDCFC3CSZXqsPWfFXyUE")
    df = conn.read()

    st.subheader("Sheet Data Preview")
    st.dataframe(df.head(10))

    # Print results. Adjusting column names to match your actual sheet.
    # The sheet contains columns like 'Customer Name' and 'Revenue'.
    name_col = 'Customer Name'
    val_col = 'Revenue'

    if name_col in df.columns and val_col in df.columns:
        st.subheader("Summary Snippet")
        for index, row in df.head(5).iterrows():
            st.write(f"**{row[name_col]}** generated a revenue of **{row[val_col]:,.2f}**")
    else:
        st.warning(f"Columns '{name_col}' or '{val_col}' not found. Available columns: {', '.join(df.columns.tolist())}")

except (SpreadsheetNotFound, WorksheetNotFound) as e:
    st.error(f"The spreadsheet or worksheet was not found. Please check the URL in `.streamlit/secrets.toml`. Details: {e}")
except Exception as e:
    st.error(f"An error occurred while connecting to Google Sheets: {e}")
    st.info("Checklist:\n1. Ensure `secrets.toml` is inside a `.streamlit` folder.\n2. The spreadsheet must be public OR you need a service account.\n3. Make sure the Google Sheets API is enabled if using a service account.")