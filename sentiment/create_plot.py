import en_core_web_sm
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from nltk.util import ngrams
import re
import pandas as pd



def common_words(df, n=10, n_gram=10, pos='NOUN', sentiment=None, filter=False, date_range=None):

    if sentiment is not None and filter:
        df = df[df['sentiment'] == sentiment].reset_index()

    nlp = en_core_web_sm.load()
    if n_gram == 1:

        corpus = ''.join(df.comment.values.tolist())
        doc = nlp(corpus)

        word_lst = []
        for token in doc:
            if not token.is_stop and not token.is_punct and token.pos_ == pos:
                word_lst.append(token.text)

        word_freq = Counter(word_lst)

        most_common = word_freq.most_common(n)


    else:
        corpus = df["comment"]
        vec = CountVectorizer(ngram_range=(n_gram,n_gram)).fit(corpus)
        bag_of_words = vec.transform(corpus)
        sum_words = bag_of_words.sum(axis=0)
        words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
        words_freq =sorted(words_freq, key = lambda x: x[1], reverse=True)

        most_common = words_freq[:n]
        print(most_common)


    img = plot_graph(df, most_common, filter=filter, sentiment=sentiment, date_range=date_range)
    return most_common, img



import re
def plot_graph(df, patterns, filter=None, sentiment=None, date_range=None):

    df = df.reset_index()

    if df.empty:
        return None

    new_df = pd.DataFrame()
    top_words = []
    for pattern in patterns:
        idx = []

        for row, data in df.iterrows():

            if re.findall(pattern[0], df.comment.iloc[row]):
                idx.append(row)
                

        if idx == []:
            continue

        else:
        
            df_temp = df.iloc[idx].groupby('sentiment').agg({'Username':'count'}).reset_index()
            df_temp['word'] = pattern[0]

            top_words.extend([pattern[0] for i in range(df_temp.sentiment.nunique())])
            new_df = new_df.append(df_temp)

    new_df['word'] = top_words



    pivot = new_df.pivot_table(index='word', columns='sentiment',values='Username').reset_index()
    cols =  pivot.columns.tolist()[1:]


    cols.sort(reverse=True)
    pivot['total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by='total', ascending=False)
    pivot = pivot.drop(['total'], axis=1)

    # show graph
    title = f'Most frequently used words for period {date_range}'
    plot = pivot[['word']+ cols].set_index('word').plot(kind='bar', stacked=True, sort_columns=False, ylabel='Frequency', title=title,rot=90, fontsize=10)


    fig = plot.get_figure()
    image_name = 'output'

    return fig


def main(df, n, n_gram, sentiment, filter,date_range):
    print(f'date range is {date_range}')
    
    patterns, img = common_words(df, n=n, n_gram=n_gram, sentiment=sentiment, filter=filter, date_range=date_range)
    return img
