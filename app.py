import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Your Spotify Wrapped",
    page_icon="🎵",
    layout="wide"
)

# --- Helper Functions ---

# ## NEW ## - Updated to handle all relevant files
def load_data(uploaded_files):
    """Loads and combines multiple streaming history JSON files."""
    data = {
        "streaming": None,
        "wrapped": None,
        "search": None
    }
    
    streaming_files = [f for f in uploaded_files if "StreamingHistory" in f.name]
    wrapped_files = [f for f in uploaded_files if "Wrapped" in f.name]
    search_files = [f for f in uploaded_files if "SearchQueries" in f.name]

    if streaming_files:
        df_list = [pd.read_json(file) for file in streaming_files]
        data["streaming"] = pd.concat(df_list, ignore_index=True)
    
    if wrapped_files:
        # Assuming one wrapped file
        data["wrapped"] = json.load(wrapped_files[0])
        
    if search_files:
        data["search"] = pd.read_json(search_files[0])
        
    return data


def clean_data(df):
    """Cleans the raw streaming data and converts timezone from UTC to US/Central."""
    df['endTime'] = pd.to_datetime(df['endTime'])
    
    # Localize the timezone-naive UTC timestamps to 'UTC'
    df['endTime'] = df['endTime'].dt.tz_localize('UTC')
    
    # Convert the UTC timestamps to 'US/Central' (CST/CDT)
    df['endTime'] = df['endTime'].dt.tz_convert('US/Central')
    
    df_filtered = df[df['msPlayed'] > 30000].copy()
    df_filtered['hour'] = df_filtered['endTime'].dt.hour
    df_filtered['day_of_week'] = df_filtered['endTime'].dt.day_name()
    return df_filtered


# --- Streamlit App ---

st.title("🎧 Your Personal Spotify Wrapped")
st.markdown("Upload your `StreamingHistory` and other JSON files to see your music taste visualized!")

# --- Sidebar for File Upload ---
with st.sidebar:
    st.header("Upload Your Data")
    # Updated file uploader text
    uploaded_files = st.file_uploader(
        "Upload your Spotify data files here. `StreamingHistory` is required.",
        accept_multiple_files=True,
        type="json",
        help="Include SearchQueries.json, Wrapped files, etc., for more insights!"
    )

if uploaded_files:
    with st.spinner("Crunching the numbers... Your Wrapped is on its way! 🎶"):
        try:
            # --- Data Processing ---
            data = load_data(uploaded_files)
            raw_df = data["streaming"]
            
            if raw_df is None:
                st.warning("Please upload at least one `StreamingHistory` file to get started.")
            else:
                df = clean_data(raw_df)

                # --- Main Page Layout ---
                st.success("Your data is ready! Here's your mid-year Wrapped:")

                # Updated tab structure
                tab_list = [
                    "📈 Overview", 
                    "🏆 Top Lists", 
                    "🕰️ Listening Habits", 
                    "🎤 Artist Deep Dive"
                ]
                tab1, tab2, tab3, tab4 = st.tabs(tab_list)

                with tab1:
                    st.header("Your Listening at a Glance")
                    col1, col2, col3 = st.columns(3)
                    total_hours = df['msPlayed'].sum() / (1000 * 60 * 60)
                    unique_songs = df['trackName'].nunique()
                    unique_artists = df['artistName'].nunique()

                    col1.metric("Total Hours Listened", f"{total_hours:.2f} hrs")
                    col2.metric("Unique Songs", f"{unique_songs}")
                    col3.metric("Unique Artists", f"{unique_artists}")
                    
                    st.markdown("---")
                    st.subheader("Listening Trend Over Time")
                    monthly_listening = df.set_index('endTime').resample('M').size()
                    st.line_chart(monthly_listening)

                with tab2:
                    st.header("Your All-Time Favorites")
                    top_10_songs = df['trackName'].value_counts().head(10)
                    top_10_artists = df['artistName'].value_counts().head(10)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Top 10 Songs")
                        st.dataframe(top_10_songs)
                    with col2:
                        st.subheader("Top 10 Artists")
                        st.dataframe(top_10_artists)
                
                with tab3:
                    st.header("When Do You Listen?")
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
                    sns.set(style="whitegrid")
                    hourly_counts = df['hour'].value_counts().sort_index()
                    sns.barplot(x=hourly_counts.index, y=hourly_counts.values, ax=ax1, palette='viridis')
                    ax1.set_title('Listening by Hour of Day', fontsize=16)
                    ax1.set_xlabel('Hour of Day')
                    ax1.set_ylabel('Number of Songs')
                    daily_counts = df['day_of_week'].value_counts().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
                    sns.barplot(x=daily_counts.index, y=daily_counts.values, ax=ax2, palette='plasma')
                    ax2.set_title('Listening by Day of Week', fontsize=16)
                    ax2.set_xlabel('Day')
                    ax2.set_ylabel('Number of Songs')
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                with tab4:
                    top_artist_name = df['artistName'].value_counts().index[0]
                    st.header(f"Artist Deep Dive: {top_artist_name}")
                    artist_df = df[df['artistName'] == top_artist_name]
                    st.subheader(f"Your Top 5 Songs by {top_artist_name}")
                    st.dataframe(artist_df['trackName'].value_counts().head(5))
                    st.subheader(f"When You Listen to {top_artist_name}")
                    fig, ax = plt.subplots(figsize=(12, 6))
                    artist_hourly = artist_df['hour'].value_counts().sort_index()
                    sns.barplot(x=artist_hourly.index, y=artist_hourly.values, ax=ax, palette='rocket')
                    ax.set_title(f'Your Listening Habits for {top_artist_name}')
                    ax.set_xlabel('Hour of Day')
                    ax.set_ylabel('Number of Songs')
                    st.pyplot(fig)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.warning("Please ensure you've uploaded valid Spotify JSON files.")

else:
    st.info("Upload your Spotify data in the sidebar to get started!")
