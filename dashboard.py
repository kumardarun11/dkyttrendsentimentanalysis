import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from wordcloud import WordCloud

# 🎨 Streamlit Page Configuration
st.set_page_config(
    page_title="DKTube Analytics: Trending Insights & Sentiment",
    page_icon="📊",
    layout="wide",
)

import os

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing! Make sure it's set in GitHub Secrets.")

print("API Key Loaded Successfully (Masked)")  # Avoid printing actual key
youtube = build("youtube", "v3", developerKey=API_KEY)

# 📌 Fetch trending videos
def get_trending_videos(region_code="US", max_results=10):
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region_code,
        maxResults=max_results
    )
    response = request.execute()
    
    videos = []
    for video in response["items"]:
        views = int(video["statistics"]["viewCount"])
        likes = int(video["statistics"].get("likeCount", 0))
        comments = int(video["statistics"].get("commentCount", 0))
        engagement = round(((likes + comments) / views) * 100, 2) if views > 0 else 0

        videos.append({
            "Title": video["snippet"]["title"],
            "Channel": video["snippet"]["channelTitle"],
            "Views": views,
            "Likes": likes,
            "Comments": comments,
            "Engagement Rate (%)": engagement,
            "Video ID": video["id"],
            "URL": f"https://www.youtube.com/watch?v={video['id']}"
        })

    return pd.DataFrame(videos)

# 📌 Fetch video comments & analyze sentiment
def get_video_comments(video_id, max_results=20):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results
    )
    response = request.execute()

    comments = []
    for comment in response["items"]:
        text = comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        sentiment_score = TextBlob(text).sentiment.polarity
        sentiment = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
        comments.append({"Comment": text, "Sentiment": sentiment})

    return pd.DataFrame(comments)

# 📌 Generate Word Cloud
def generate_wordcloud(df):
    text = " ".join(df["Comment"])
    wordcloud = WordCloud(width=800, height=400, background_color="black").generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

# 🎨 Custom Styling
st.markdown("""
    <style>
        .stDataFrame {border-radius: 10px; overflow: hidden;}
        .big-font { font-size:20px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 🏠 Sidebar Configuration
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/ef/Youtube_logo.png", width=180)
st.sidebar.title("📊 YouTube Trends")
region_code = st.sidebar.selectbox("🌍 Select Region", ["US", "IN", "UK", "CA", "AU", "DE", "FR"])
max_results = st.sidebar.slider("🎬 Number of Videos", 5, 20, 10)

# 📊 Fetch & Display Trending Videos
st.title("🔥 DK YouTube Trends & Sentiment Analysis")
trending_df = get_trending_videos(region_code, max_results)

# 🏆 Trending Videos Table with Clickable Titles (Styled & Scrollable with Fixed Headers)
st.subheader(f"🎬 Top {max_results} Trending Videos in {region_code}")

# Convert video titles into clickable links
trending_df["Title"] = trending_df.apply(lambda row: f'<a href="{row["URL"]}" target="_blank">{row["Title"]}</a>', axis=1)

# Apply custom styling for scrollable table with fixed headers
st.markdown("""
    <style>
        .scrollable-table-container {
            max-height: 400px;  /* Set a fixed height */
            overflow-y: auto;   /* Enable scrolling */
            border: 1px solid #444;
        }
        .scrollable-table-container thead th {
            position: sticky;
            top: 0;
            background-color: #ff0000; /* YouTube red */
            color: white;
            z-index: 2;
        }
        .scrollable-table-container table {
            width: 100%;
            border-collapse: collapse;
        }
        .scrollable-table-container th, .scrollable-table-container td {
            border: 1px solid #444;
            padding: 10px;
            text-align: center;
        }
        .scrollable-table-container td {
            background-color: #222;
            color: white;
        }
        .scrollable-table-container a {
            color: #1E90FF;
            text-decoration: none;
            font-weight: bold;
        }
        .scrollable-table-container a:hover {
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# Wrap the table inside a scrollable div
st.markdown(f'<div class="scrollable-table-container">{trending_df.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)


# 📊 Data Visualization
st.subheader("📈 Trending Videos Insights")

# 🔥 Views Chart
fig = px.bar(trending_df, x="Views", y="Title", orientation="h", title="🔝 Top Trending Videos by Views", color="Views", color_continuous_scale="blues")
st.plotly_chart(fig, use_container_width=True)

# ❤️ Engagement Rate Chart
fig = px.scatter(trending_df, x="Likes", y="Comments", size="Engagement Rate (%)", color="Engagement Rate (%)",
                 title="💬 Engagement Rate vs. Likes & Comments",
                 hover_data=["Title", "Channel", "URL"], size_max=50)
st.plotly_chart(fig, use_container_width=True)

# 💬 Comment Sentiment Analysis
st.subheader("💬 Comments Sentiment Analysis")
video_id = st.selectbox("🎥 Select a Video", trending_df["Video ID"])
comments_df = get_video_comments(video_id)

# Apply custom styling for a scrollable sentiment table with fixed headers
st.markdown("""
    <style>
        .scrollable-comments-container {
            max-height: 400px;  /* Set a fixed height */
            overflow-y: auto;   /* Enable scrolling */
            border: 1px solid #444;
        }
        .scrollable-comments-container thead th {
            position: sticky;
            top: 0;
            background-color: #ff0000; /* YouTube red */
            color: white;
            z-index: 2;
        }
        .scrollable-comments-container table {
            width: 100%;
            border-collapse: collapse;
        }
        .scrollable-comments-container th, .scrollable-comments-container td {
            border: 1px solid #444;
            padding: 10px;
            text-align: center;
        }
        .scrollable-comments-container td {
            background-color: #222;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Wrap the table inside a scrollable div
st.markdown(f'<div class="scrollable-comments-container">{comments_df.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)


# 📊 Sentiment Distribution Chart
st.subheader("📊 Sentiment Distribution Chart")
sentiment_counts = comments_df["Sentiment"].value_counts()

fig, ax = plt.subplots(figsize=(5, 3.5))  # Adjusted to be proportional
sns.barplot(x=sentiment_counts.index, y=sentiment_counts.values, palette="magma", ax=ax)
ax.set_xlabel("Sentiment")
ax.set_ylabel("Count")

# Prevent auto-scaling when resizing
st.pyplot(fig, use_container_width=False)

# ☁ Word Cloud (Balanced Size)
st.subheader("☁ Word Cloud of Comments")

text = " ".join(comments_df["Comment"])
wordcloud = WordCloud(width=700, height=350, background_color="black").generate(text)  # Balanced size

fig, ax = plt.subplots(figsize=(6, 3.5))  # Adjusted to be proportional
ax.imshow(wordcloud, interpolation="bilinear")
ax.axis("off")

# Prevent auto-scaling when resizing
st.pyplot(fig, use_container_width=False)

# 📥 Data Export Section
st.sidebar.subheader("📥 Export Data")
if st.sidebar.button("Download Trending Videos CSV"):
    trending_df.to_csv("trending_videos.csv", index=False)
    st.sidebar.success("✅ Downloaded trending_videos.csv!")

if st.sidebar.button("Download Comments CSV"):
    comments_df.to_csv("video_comments.csv", index=False)
    st.sidebar.success("✅ Downloaded video_comments.csv!")

# ℹ Developer Info
st.sidebar.markdown("---")
st.sidebar.subheader("👨‍💻 Developer Info")
st.sidebar.write("**Name:** D ARUN KUMAR")
st.sidebar.write("📧 Email: kumardarun11@gmail.com")
st.sidebar.write("[GitHub](https://github.com/kumardarun11) | [LinkedIn](https://linkedin.com/in/kumardarun11)")
