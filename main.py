import streamlit as st
from streamlit_gsheets import GSheetsConnection
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Note: Providing both `worksheet` and `gid` is redundant.
    # The library prioritizes `worksheet`. I've removed `gid` for clarity.
    # If you intend to select by GID, remove `worksheet` and use `gid` instead.
    df = conn.read()

    st.dataframe(df.head(10))

    # Print results. This part assumes your sheet has 'name' and 'pet' columns.
    # It's good practice to check if columns exist before using them.
    if 'name' in df.columns and 'pet' in df.columns:
        for row in df.itertuples():
            st.write(f"{row.name} has a :{row.pet}:")
    else:
        st.warning("The sheet does not contain 'name' and 'pet' columns. Cannot display results as intended.")

except (SpreadsheetNotFound, WorksheetNotFound) as e:
    st.error(f"The spreadsheet or worksheet was not found. Please check the ID and name. Details: {e}")
except Exception as e:
    st.error(f"An error occurred while connecting to Google Sheets: {e}")
    st.info("Please double-check your `secrets.toml` configuration, sheet sharing permissions, and that the Google Sheets & Drive APIs are enabled.")