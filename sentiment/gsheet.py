import pygsheets
import pandas as pd
gc = pygsheets.authorize(service_file='sentiment/creds.json')


def get_sheet(new_df,src):
    date_range = None
    sh = gc.open('User Sentiment')

    if src == 'ig':
        wks = sh.worksheet('title','IG Sentiment')
    elif src == 'fb': 
        wks = sh.worksheet('title','FB Sentiment')

    existing_df = wks.get_as_df()
    
    new_df['Time'] = pd.to_datetime(new_df["Time"], format = "%Y-%m-%d %H:%M") # to be commented out
    new_df['Time'] = new_df['Time'].dt.date


    df = pd.concat([new_df,existing_df])

    df['Time'] = pd.to_datetime(df["Time"], format = "%Y-%m-%d")

    min_day = min(df['Time'])
    max_day = max(df['Time'])

    date_range = f'{min_day.day}/{min_day.month}/{min_day.year} till {max_day.day}/{max_day.month}/{max_day.year}'
    print(date_range)

    return df, date_range


    





def main(new_df, src):
    df, date_range = get_sheet(new_df, src)
    return df, date_range

