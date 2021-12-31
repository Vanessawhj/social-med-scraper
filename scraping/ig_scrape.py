import instaloader
import datetime 
from tqdm import tqdm
from itertools import takewhile, dropwhile
import pytz
import pandas as pd
import os
import glob 
import json
import shutil
import re
from pathlib import Path


local_tz = pytz.timezone("Asia/Kuala_Lumpur")

# Set path 
path = os.getcwd()
print(f'parent file: {Path(path)}')
os.chdir(path)
file = "ig_comments" # folder name to be saved
new_path = os.path.join(path, file)

try:
    print(new_path)
    shutil.rmtree(new_path)
except:
    pass




def details(username, password, HANDLE, UNTIL, SINCE):
    # Get instance
    L = instaloader.Instaloader(download_videos=False,download_geotags=False,download_pictures=False,compress_json=False,download_comments=True, max_connection_attempts=5)
    L.login(username, password)        # (login)


    START_TIME = datetime.datetime.now(tz=local_tz)


    # Get the handle 
    profile = instaloader.Profile.from_username(L.context, HANDLE)
    posts = profile.get_posts()



    # # Manual key in dates
    # SINCE = datetime.datetime(2021, 7, 2)
    # UNTIL = datetime.datetime(2021, 7, 3)

    # # input days 
    # days = 1

    # SINCE = datetime.datetime.now()
    # UNTIL = SINCE - datetime.timedelta(days)

    UNTIL = datetime.datetime.strptime(UNTIL, '%d/%m/%Y')
    SINCE = datetime.datetime.strptime(SINCE, '%d/%m/%Y')

    UNTIL = datetime.datetime(UNTIL.year, UNTIL.month, UNTIL.day)
    SINCE = datetime.datetime(SINCE.year, SINCE.month, SINCE.day)

    

    for post in tqdm(takewhile(lambda p: p.date > UNTIL, dropwhile(lambda p: p.date > SINCE, posts))):
        if post.comments > 15000:
            continue

        else:
            L.download_post(post, file) # save as folder name
        

    END_TIME = datetime.datetime.now(tz=local_tz)
    print(f"Execution Time (hh:mm:ss.ms) {END_TIME-START_TIME}")


def output():
    # go to child directory
    new_path = path+'/'+file
    os.chdir(new_path)

    # Open only json files containing comments
    folder = glob.glob('*_comments.json')
    combined_files = open("combined_files.json", "a")


    ''' To combine all objects into a list to be parsed later '''
    combined_files.write('[')

    for idx in range(len(folder)):
        files = folder[idx]
    
        with open(files, "r") as f:
            data = f.read()

            # Remove [] for each new post
            data = data[1:-1] + ','
            combined_files.write(data)
        

    data = data[1:-1]
    combined_files.write(data)
    combined_files.write(']')
    combined_files.close()


    f = open("combined_files.json", "r")    
    data = json.load(f)

    with open("ig_comments.json", "a", encoding="utf-8") as comments:
        for key in data:
            text = key["text"]
            print(text)

            comments.write(text)
            comments.write("\n")

        comments.close()

    f = open("combined_files.json", "r")

    df = pd.DataFrame(columns=["Time","Comment","Username"])
    data = json.load(f)

    for idx in range(len(data)):
        key=data[idx]
        lst=[]

        lst.append(datetime.datetime.fromtimestamp(key["created_at"]))
        lst.append(key["text"])
        lst.append(key["owner"]["username"])
        df.loc[idx] = lst

    df["Platform"] = "IG" 

    os.chdir(Path(path))

    return df

def filter_comments(df):
    pattern = '(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'
    lst = []
    df = df.drop_duplicates()

    for row, data in df.iterrows():

        text = str(data['Comment'])

        # remove url
        if (re.findall(pattern,text)) and len(text.split()) < 10:
            continue

        # remove spam
        elif len(text.split()) < 3:
            continue
        
        else:
            lst.append(data.values.tolist())

    new_df = pd.DataFrame()
    new_df = new_df.append(lst)
    new_df = new_df.rename({0:'Time',1:'Comment',2:'Username',3:'Platform'},axis=1)

    new_df['Time'] = pd.to_datetime(df["Time"], format = "%Y-%m-%d %H:%M")
    new_df['Time'] = new_df['Time'].dt.date.astype(str)

    return new_df



def main(HANDLE, startdate, enddate):


    f = open("scraping/logins.json")
    data = json.load(f)

    username = data['instagram']['email']
    password = data['instagram']['password']

    print(f'Starting date: {startdate}\nEnding date: {enddate}')
    details(username, password, HANDLE, startdate, enddate)

    df = output()
    df = filter_comments(df)
    print(df)
    return df


