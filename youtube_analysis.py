from googleapiclient.discovery import build
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import os

# Replace with your YouTube API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Missing API Key! Set GOOGLE_API_KEY in GitHub Secrets.")

print("API Key Loaded Successfully")  # Avoid printing actual key for security

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=API_KEY)

# Function to get trending videos
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
        engagement_rate = round(((likes + comments) / views) * 100, 2) if views > 0 else 0

        videos.append({
            "Title": video["snippet"]["title"],
            "Views": views,
            "Likes": likes,
            "Comments": comments,
            "Engagement Rate (%)": engagement_rate,
            "Channel": video["snippet"]["channelTitle"],
            "Video ID": video["id"],
            "URL": f"https://www.youtube.com/watch?v={video['id']}"
        })

    df = pd.DataFrame(videos)
    df = df.sort_values(by="Views", ascending=False)
    return df

# Function to analyze video comments
def get_video_comments(video_id, max_results=10):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results
    )
    response = request.execute()

    comments = []
    for comment in response["items"]:
        text = comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        author = comment["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
        sentiment_score = TextBlob(text).sentiment.polarity  # Sentiment (-1 to 1)
        sentiment = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"

        comments.append({"Author": author, "Comment": text, "Sentiment": sentiment})

    df = pd.DataFrame(comments)
    return df

# Function to search for videos by keyword
def search_videos(query, max_results=10):
    request = youtube.search().list(
        part="snippet",
        q=query,
        maxResults=max_results,
        type="video"
    )
    response = request.execute()

    videos = []
    for video in response["items"]:
        videos.append({
            "Title": video["snippet"]["title"],
            "Channel": video["snippet"]["channelTitle"],
            "Video ID": video["id"]["videoId"],
            "URL": f"https://www.youtube.com/watch?v={video['id']['videoId']}"
        })

    return pd.DataFrame(videos)

# Function to visualize trending videos
def plot_trending_videos(df):
    plt.figure(figsize=(12, 6))
    sns.barplot(y=df["Title"], x=df["Views"], palette="coolwarm")
    plt.xlabel("Views (millions)")
    plt.ylabel("Video Title")
    plt.title("Top Trending Videos by Views")
    plt.show()

# Function to visualize engagement rates
def plot_engagement(df):
    plt.figure(figsize=(10, 5))
    sns.barplot(y=df["Title"], x=df["Engagement Rate (%)"], palette="magma")
    plt.xlabel("Engagement Rate (%)")
    plt.ylabel("Video Title")
    plt.title("Top Trending Videos by Engagement")
    plt.show()

# Function to visualize comment sentiment
def plot_sentiment_distribution(df):
    sentiment_counts = df["Sentiment"].value_counts()
    plt.figure(figsize=(6, 4))
    sns.barplot(x=sentiment_counts.index, y=sentiment_counts.values, palette="viridis")
    plt.xlabel("Sentiment")
    plt.ylabel("Count")
    plt.title("Comment Sentiment Distribution")
    plt.show()

# Function to generate a word cloud from comments
def generate_wordcloud(df):
    text = " ".join(df["Comment"])
    wordcloud = WordCloud(width=800, height=400, background_color="black").generate(text)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Word Cloud of Video Comments")
    plt.show()

# Function to export data to CSV
def export_to_csv(df, filename):
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")

# Run the program
if __name__ == "__main__":
    print("Fetching trending videos...\n")
    trending_df = get_trending_videos()
    print(trending_df)

    # Export trending video data
    export_to_csv(trending_df, "trending_videos.csv")

    # Plot trending videos
    plot_trending_videos(trending_df)
    plot_engagement(trending_df)

    # Get comments & analyze sentiment for the top trending video
    video_id = trending_df.iloc[0]["Video ID"]
    print(f"\nFetching comments for: {trending_df.iloc[0]['Title']}\n")
    comments_df = get_video_comments(video_id)
    print(comments_df)

    # Export comments data
    export_to_csv(comments_df, "video_comments.csv")

    # Visualize sentiment
    plot_sentiment_distribution(comments_df)
    generate_wordcloud(comments_df)

    # Search for videos on a topic
    search_query = "AI technology"
    print(f"\nSearching videos for: {search_query}\n")
    search_results_df = search_videos(search_query)
    print(search_results_df)

    # Export search results
    export_to_csv(search_results_df, "search_results.csv")
