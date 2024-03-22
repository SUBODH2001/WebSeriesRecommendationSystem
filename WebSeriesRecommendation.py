import streamlit
import requests
from bs4 import BeautifulSoup
import pandas as pd 
import gspread
import streamlit as st
import schedule
from textblob import TextBlob
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import time


class Series(object):

    def __init__(self) -> None:

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        }
        self.data = []
    
    def url(self, genre = None, from_year = None, to_year = None) -> None:
        if not (genre or from_year or to_year):
            self.recommend(link="https://www.imdb.com/search/keyword/?keywords=web-series&sort=moviemeter,asc&mode=detail&page=1&ref_=kw_ref_gnr")

        elif genre and not (from_year or to_year):
            link = "https://www.imdb.com/search/keyword/?keywords=web-series&mode=detail&page=1&ref_=kw_ref_gnr&sort=moviemeter,asc&genres="
            while genre:
                g = genre.pop()
                link+=g
                if genre:
                    link+="%2C"
            self.recommend(link=link)
        
        elif from_year and not(genre or to_year):
            self.recommend(f"https://www.imdb.com/search/keyword/?keywords=web-series&mode=detail&page=1&ref_=kw_ref_yr&sort=moviemeter,asc&release_date={from_year}%2C")
        
        elif to_year and not(genre or from_year):
            self.recommend(f"https://www.imdb.com/search/keyword/?keywords=web-series&mode=detail&page=1&ref_=kw_ref_yr&sort=moviemeter,asc&release_date=%2C{to_year}")
        
        elif to_year and from_year and not(genre):
            self.recommend(f"https://www.imdb.com/search/keyword/?keywords=web-series&mode=detail&page=1&ref_=kw_ref_yr&sort=moviemeter,asc&release_date={from_year}%2C{to_year}")
        
        elif to_year and genre and not(from_year):
            link = "https://www.imdb.com/search/keyword/?keywords=web-series&mode=detail&page=1&ref_=kw_ref_gnr&sort=moviemeter,asc&genres="
            while genre:
                g = genre.pop()
                link+=g
                if genre:
                    link+="%2C"
            link += f"&release_date=%2C{to_year}"
            self.recommend(link=link)

        elif from_year and genre and not(to_year):
            link = "https://www.imdb.com/search/keyword/?keywords=web-series&mode=detail&page=1&ref_=kw_ref_gnr&sort=moviemeter,asc&genres="
            while genre:
                g = genre.pop()
                link+=g
                if genre:
                    link+="%2C"
            link += f"&release_date={from_year}%2C"
            self.recommend(link=link)
        else:
            link = "https://www.imdb.com/search/keyword/?keywords=web-series&mode=detail&page=1&ref_=kw_ref_gnr&sort=moviemeter,asc&genres="
            while genre:
                g = genre.pop()
                link+=g
                if genre:
                    link+="%2C"
            link += f"&release_date={from_year}%2C{to_year}"
            self.recommend(link=link)

    def sentiments(self:object, link: str) -> str:
        sentiments = []
        try:
            soup = BeautifulSoup(requests.get(link).text, "html.parser")
            for i in soup.find_all("div", class_ = "text show-more__control"):
                sentiments.append(i.text)

            all_reviews = ' '.join(sentiments)
            blob = TextBlob(all_reviews)
            sentiment = "Positive" if blob.sentiment.polarity > 0 else "Negative" if blob.sentiment.polarity < 0 else "Neutral"
            parser = PlaintextParser.from_string(all_reviews, Tokenizer("english"))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, sentences_count=2) 
            return sentiment, " ".join(str(sentence) for sentence in summary)
        except:
            return "Neutral", "Sentiment can't be analysed due to few reviews"  
        

    def recommend(self, link):
        
        try:
            soup = BeautifulSoup(requests.get(link).text, "html.parser")
            n=0
            for item in soup.find("div", class_ ="lister-list").find_all("div", class_ = "lister-item mode-detail"):
                id = item.find("div", class_ = "lister-item-image ribbonize").attrs["data-tconst"]
                title  = item.find("h3")
                title = (title.text[title.text.index(".")+1:title.text.index("(")])[1:-1]
                genre = item.find('span', class_='genre').text.strip()
                Votes = item.find_all("p")[-1].find_all("span")[-1].text.strip()
                link = f"https://www.imdb.com/title/{id}/reviews?ref_=tt_urv"
                sentiment, summary = self.sentiments(link)
                self.data.append([title, genre, Votes, sentiment, summary])
                n+=1
                if n==3:
                    break
        except Exception as e:
            print(f"Something went wrong: {e}")
        
        df = pd.DataFrame(self.data, columns=['title', 'genre', 'Votes', 'sentiment', 'summary'])
        df.set_index("title", inplace=True)
        st.table(df)
        self.send_to_sheet()


    def send_to_sheet(self):
        try:
            #Credentials goes here
            sheet = sh.worksheet("WebData")
            df = pd.DataFrame(self.data, columns=['title', 'genre', 'runtime', 'sentiment', 'summary'])
            data = df.values.tolist()
            sheet.update(range_name="A2", values=data)
            print("Dashboard is also updated")

        except Exception as e:
            print(f"Wasn't able to add to sheet might be some error: {e}")
        


def main():
    st.set_page_config(page_title="Web-Series Recommendation",layout="centered", page_icon="random")
    title = "What would you like to watch today?"
    st.title(title.upper())
    genre = st.multiselect("Select Genre", [
        "Comedy",
        "Drama",
        "Short",
        "Talk-Show",
        "Animation",
        "Documentary",
        "Fantasy",
        "Action",
        "Sci-Fi",
        "Adventure",
        "Horror",
        "Romance",
        "News",
        "Thriller",
        "Music",
        "Mystery",
        "Family",
        "Crime",
        "History",
        "Game-Show",
        "Sport",
        "Musical",
        "Biography",
        "War",
        "Western"
    ])
    from_year = st.number_input("From Year", min_value=1990, max_value=2024)
    to_year = st.number_input("To Year", min_value=from_year, max_value=2024)
    if st.button("Get Web-Series"):
        webseries = Series()
        webseries.url(genre, from_year, to_year)

def job():
    main()

schedule.every(7).days.do(job)

main()

while True:
    schedule.run_pending()
    time.sleep(1)