import pytz

import re
import pandas as pd 
import numpy as np


import pandas as pd
from textblob import TextBlob
import numpy as np
from tqdm import tqdm
tqdm.pandas()
import spacy
from langdetect import detect_langs
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from spacy.matcher import Matcher
# python3 -m spacy download en_core_web_sm





local_tz = pytz.timezone('Asia/Kuala_Lumpur')



def detect_lg(x):
    ''' to predict the language of the comment'''
    try:
        lang = detect_langs(x)
        x = str(lang[0])[:2]

        if x in ['da','so','nl']:
            return "en"

        elif x in ['tl','no','tr','hr','et','cy']:
            return "id"

        elif x in ['zh','ch','ko']:
            return "zh"

        elif x == "en":
            return "en"
        
        elif x == "id":
            return "id"

    except:
        return np.nan

    



def sentiment_scores(sentence):
    ''' to predict sentiment scores and polarity'''

    # Create a SentimentIntensityAnalyzer object.
    sid_obj = SentimentIntensityAnalyzer()
    sentiment_dict = sid_obj.polarity_scores(str(sentence))
    
    
    if sentiment_dict['compound'] <  0 :
        return "Negative"
    
    elif sentiment_dict['neu'] >= sentiment_dict['pos'] + 0.1:
        return "Neutral"
    else :
        return "Positive"


def polarity(text):
    return TextBlob(str(text)).sentiment.polarity


def revised_polarity_score(df):
    scores = []
    analyzer = SentimentIntensityAnalyzer()
    i=0
    for index, row in tqdm(df.iterrows()):
        i+=1
        vs = analyzer.polarity_scores(str(row["comment"]))

        if row["sentiment"] == "Negative" and row["polarity_score"] >= 0:
            scores.append(vs["compound"])

        elif row["polarity_score"] > 0.5 and row["comment"] != "Positive":
            scores.append(vs["compound"]*vs["neu"])

        else:
            scores.append(row["polarity_score"])

    df["new_score"] = scores
    return df



def revised_sentiment(df):
    sentiment = []
    
    for index, row in tqdm(df.iterrows()):
        
        if row["polarity_score"] < -0.3 and row["sentiment"] != "Negative":
            sentiment.append("Negative")

        elif row["new_score"] > 0.4 and row["sentiment"] != "Positive":
            sentiment.append("Positive")

        else:
            sentiment.append(row["sentiment"])

    df["sentiment"] = sentiment
    return df    


def get_sentiment(df):
    
    # predict sentiment (not using 'translated')
    df['sentiment']= df['comment'].progress_apply(lambda x : sentiment_scores(x))

    # predict polarity
    df['polarity_score'] = df['comment'].progress_apply(lambda x : polarity(x))

    # revise sentiment and polarity scores
    df = revised_polarity_score(df)
    df = revised_sentiment(df)    

    # clean the reviews, remove \n in reviews
    df["comment"] = df.comment.replace(r'\\n',' ', regex=True)

    return df




def label_category(x):
    
    lst = set()
    packaging = ["packaging","packing"]
    delivery = ["courier","delivery","shipping","ship","deliver","next day"]
    product = ["condition","product","quality","expiry","lasting","item"]
    seller = ["seller","service","stock"]
    price = ["cheap","price","prices","deal","value","offer","discount"]

    test_list = ["condition","deliver?\w+", "product","pack\w+","service","quality","price?\w+","cheap","deal","stock","value","expiry","lasting","ship?\w+","offer","n\w*t day","item","seller","discount"]
    temp ='|'.join(test_list)


    r = re.compile(temp)
    label = ', '.join(x)
    text = r.findall(label)

    for word in text:
        if word in packaging:
            lst.add("packaging")

        elif word in product:
            lst.add("product")

        elif word in delivery:
            lst.add("delivery")

        elif word in seller:
            lst.add("seller")

        elif word in price:
            lst.add("price")

    return list(lst)



def label_extraction(df):
    nlp = spacy.load("en_core_web_sm", exclude=["ner", "parser", "lemmatizer"])

    matcher = Matcher(nlp.vocab)

    patterns = [[{"POS": "ADJ"}, {"POS": "NOUN"}],
                [{"POS": "VERB"}, {"POS": "NOUN"}],
                [{"POS": "ADV"}, {"POS": "NOUN"}],
            [{"LOWER":{"REGEX":"ship|pack|pric|cheap|deliver"}}]]

    def lemmatize_pipe(doc):
        matched = set()
        for pattern in patterns:
            matcher.add("label", [pattern])
            matches = matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]  # The matched span
                matched.add(span.text)

        return list(matched)

    def preprocess_pipe(texts):
        preproc_pipe = []
        for doc in nlp.pipe(texts, batch_size=20):
            preproc_pipe.append(lemmatize_pipe(doc))
        return preproc_pipe

    df['labels'] = preprocess_pipe(df['comment'])
    print('extracted labels')

    df["category"] = df["labels"].progress_apply(lambda x: label_category(x))
    df['category'] = [','.join(map(str, l)) for l in df['category']]
    df['category'] = df.category.apply(lambda x: x.replace(',','*'))
    print('splitting labels')
    temp_df = df['category'].str.get_dummies(sep='*')
    df = df.reset_index()
    temp_df = temp_df.reset_index()
    df = df.merge(temp_df,how="left",left_on="index",right_on="index").drop(['category','index'],axis=1)
    print(df)
    return df

def main(df):
    filter_eng = True

    df = df.rename({"Comment":"comment"},axis=1)

    df["language"] = df.comment.progress_apply(lambda x: detect_lg(x))


    if filter_eng:
        df = df[df['language'] == 'en']

    # removed NaN for those which are not translated
    df = df[~df.comment.isnull()]

    # get sentiment
    df = get_sentiment(df)

    # get labels
    df = label_extraction(df)

    print(df)
    return df




