import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Instagram Hashtag Analyzer", layout="wide")
st.title("Instagram Hashtag Analysis 📊")

def get_count(tag):
    url = f"https://www.instagram.com/explore/tags/{tag}"
    try:
        s = requests.get(url, timeout=10)  # Added timeout
        s.raise_for_status()
        soup = BeautifulSoup(s.content, "html.parser")
        meta_tags = soup.find_all("meta")
        if len(meta_tags) > 6:
            content = meta_tags[6]["content"]
            count_str = content.split(" ")[0].replace("K", "000").replace("B", "000000000").replace("M", "000000").replace(".", "")
            return int(count_str)
        else:
            return 0
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {url}: {e}")
        return 0
    except (IndexError, KeyError, ValueError) as e:
        st.error(f"Error parsing Instagram data for {tag}: {e}")
        return 0

def get_best(tag, topn):
    url = f"https://best-hashtags.com/hashtag/{tag}/"
    try:
        s = requests.get(url, timeout=10) #added timeout
        s.raise_for_status()
        soup = BeautifulSoup(s.content, "html.parser")
        tags_div = soup.find("div", {"class": "tag-box tag-box-v3 margin-bottom-40"})
        if tags_div:
            tags = tags_div.text.split()[:topn]
            return [tag for tag in tags]
        else:
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching best-hashtags URL: {e}")
        return []

def load_data():
    try:
        with open("database.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        data = {"hashtag_data": {}}
        with open("database.json", "w") as f:
            json.dump(data, f, indent=4)
        return data

data = load_data()

with st.sidebar:
    st.header("Hashtag Configuration")
    num_tags = st.number_input("Number of Tags", 1, 30, 5)
    tags = []
    sizes = []
    for i in range(num_tags):
        col1, col2 = st.columns(2)
        tags.append(col1.text_input(f"Tag {i+1}", key=f"tag_{i}"))
        sizes.append(col2.number_input(f"Top-N {i+1}", 1, 10, 5, key=f"size_{i}"))

if st.button("Analyze Hashtags"):
    tab_names = ["All Hashtags"] + tags
    tag_tabs = st.tabs(tab_names)
    all_hashtags = []
    hashtag_data = []

    with tag_tabs[0]:
        st.subheader("Combined Hashtags")

    for i, tag in enumerate(tags):
        hashtags = get_best(tag, sizes[i])
        for hashtag in hashtags:
            if hashtag in data["hashtag_data"]:
                hashtag_count = data["hashtag_data"][hashtag]
            else:
                hashtag_count = get_count(hashtag.replace("#", ""))
                data["hashtag_data"][hashtag] = hashtag_count
            hashtag_data.append((f"{hashtag}<br>{hashtag_count:,}", hashtag_count))
        all_hashtags.extend(hashtags)

        with tag_tabs[i + 1]:
            st.subheader(f"Hashtags for {tag}")
            st.text_area("Suggested Hashtags", " ".join(hashtags), height=150)

    with tag_tabs[0]:
        st.text_area("All Suggested Hashtags", " ".join(all_hashtags), height=200)

    st.header("Hashtag Popularity Analysis")
    df = pd.DataFrame(hashtag_data, columns=["hashtag", "count"])

    df['count'] = pd.to_numeric(df['count'].str.split('<br>').str[1].str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    df['hashtag'] = df['hashtag'].str.split('<br>').str[0]
    df = df[df['count'] > 0].sort_values("count", ascending=False)

    if not df.empty:
        fig = px.bar(df, x='hashtag', y='count', title="Hashtag Popularity", labels={'count': 'Post Count', 'hashtag': 'Hashtag'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid hashtag data to display.")
        st.write(hashtag_data)

    with open("database.json", "w") as f:
        json.dump(data, f, indent=4)
