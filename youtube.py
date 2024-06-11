import streamlit as st
from googleapiclient.discovery import build
import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
import plotly.express as px

# Function to clean comments
def clean_comment(comment):
    comment = emoji.replace_emoji(comment, replace='')
    comment = re.sub(r'http\S+', '', comment)
    comment = re.sub(r'[^A-Za-z0-9\s]+', '', comment)
    return comment

# Function to get YouTube comments
def get_youtube_comments(video_id, api_key, max_results=100):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            textFormat="plainText"
        )
        response = request.execute()
        comments = [item['snippet']['topLevelComment']['snippet']['textDisplay'] for item in response['items']]
        return comments
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

# Function to get video description
def get_video_description(video_id, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        description = response['items'][0]['snippet']['description']
        return description
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "No description available."

# Extract video ID from URL
def extract_video_id(url):
    video_id_match = re.search(r'(?:youtu\.be/|youtube\.com(?:/embed/|/v/|/watch\?v=|/watch\?.+&v=))([^&]{11})', url)
    if video_id_match:
        return video_id_match.group(1)
    else:
        return None

# Function to provide recommendations
def provide_recommendation(positive, negative, total, age):
    if total == 0:
        return "Not enough comments to provide a recommendation."
    
    positive_ratio = positive / total
    negative_ratio = negative / total

    if age < 13:  # Children
        if positive_ratio > 0.8:
            return "Highly recommended for children."
        elif positive_ratio > 0.5:
            return "Recommended for children (12-18)."
        elif positive_ratio > 0.3:
            return "Recommended for adults."
        elif negative_ratio > 0.5:
            return "Not recommended for children."
        else:
            return "Mixed reviews. Suitable for mature audiences."
    elif 13 <= age <= 18:  # Teens
        if positive_ratio > 0.7:
            return "Highly recommended for teens."
        elif positive_ratio > 0.5:
            return "Recommended for most teens."
        elif negative_ratio > 0.5:
            return "Not recommended for teens."
        else:
            return "Mixed reviews. Suitable for mature audiences."
    elif 19 <= age <= 64:  # Adults
        if positive_ratio > 0.7:
            return "Highly recommended for adults."
        elif positive_ratio > 0.5:
            return "Recommended for most adults."
        elif negative_ratio > 0.5:
            return "Not recommended for adults."
        else:
            return "Mixed reviews. Suitable for mature audiences."
    else:  # Aged people
        if positive_ratio > 0.8:
            return "Highly recommended for aged people."
        elif positive_ratio > 0.5:
            return "Recommended for aged people."
        elif negative_ratio > 0.5:
            return "Not recommended for aged people."
        else:
            return "Mixed reviews. Suitable for mature audiences."

# Streamlit app
st.title("YouTube Comments Sentiment Analysis with Recommendations")

# Custom CSS
st.markdown(
    """
    <style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
    }
    .stTextInput input {
        border: 2px solid #4CAF50;
    }
    .stSlider .stSliderTrack {
        background-color: #4CAF50;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Input field for YouTube video URL
video_url = st.text_input("Enter the YouTube video URL")

# Input field for child age
child_age = st.slider("Enter your age", min_value=5, max_value=100, value=13, step=1)

# Fixed YouTube API key
api_key = 'YOUR_API_KEY_HERE'

if st.button("Analyze"):
    if video_url:
        video_id = extract_video_id(video_url)
        if video_id:
            # Show loading spinner while fetching data
            with st.spinner('Fetching data...'):
                # Get comments
                comments = get_youtube_comments(video_id, api_key)
                # Get video description
                description = get_video_description(video_id, api_key)
                
                if comments:
                    # Clean comments
                    cleaned_comments = [clean_comment(comment) for comment in comments]
                    
                    # Sentiment analysis
                    analyzer = SentimentIntensityAnalyzer()
                    sentiments = [analyzer.polarity_scores(comment) for comment in cleaned_comments]
                    
                    # Aggregate sentiment scores
                    positive = sum([s['pos'] for s in sentiments])
                    neutral = sum([s['neu'] for s in sentiments])
                    negative = sum([s['neg'] for s in sentiments])
                    compound = sum([s['compound'] for s in sentiments])
                    
                    # Provide recommendation
                    total_comments = len(comments)
                    recommendation = provide_recommendation(positive, negative, total_comments, child_age)
                    
                    # Display results
                    st.subheader("Video Description")
                    st.write(description)
                    
                    st.subheader("Sentiment Analysis")
                    st.write(f"Positive sentiment: {positive}")
                    st.write(f"Neutral sentiment: {neutral}")
                    st.write(f"Negative sentiment: {negative}")
                    st.write(f"Compound sentiment: {compound}")
                    
                    st.subheader("Recommendation")
                    st.write(recommendation)

                    # Sentiment distribution
                    sentiment_distribution = {
                        'Sentiment': ['Positive', 'Neutral', 'Negative'],
                        'Count': [positive, neutral, negative]
                    }
                    df_sentiment = pd.DataFrame(sentiment_distribution)

                    # Plotly bar chart
                    fig = px.bar(df_sentiment, x='Sentiment', y='Count', title="Sentiment Distribution", color='Sentiment')
                    st.plotly_chart(fig)

                    # Create word cloud
                    all_comments = ' '.join(cleaned_comments)
                    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_comments)
                    
                    # Display word cloud
                    plt.figure(figsize=(10, 6))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis('off')
                    st.pyplot(plt)

                    # Plotly pie chart
                    fig = px.pie(names=['Positive', 'Neutral', 'Negative'], values=[positive, neutral, negative], title='Sentiment Analysis of Comments')
                    st.plotly_chart(fig)

                    # Display comments with filtering options
                    st.subheader("Comments")
                    sentiment_filter = st.selectbox("Filter comments by sentiment", ["All", "Positive", "Neutral", "Negative"])
                    filtered_comments = comments
                    if sentiment_filter != "All":
                        sentiment_mapping = {"Positive": "pos", "Neutral": "neu", "Negative": "neg"}
                        sentiment_key = sentiment_mapping[sentiment_filter]
                        filtered_comments = [comment for comment, sentiment in zip(comments, sentiments) if sentiment[sentiment_key] > 0.5]

                    for comment in filtered_comments:
                        st.write(comment)
                else:
                    st.write("No comments found for the given video URL.")
        else:
            st.write("Invalid YouTube video URL.")