import os
import pytz
import datetime
import time
import random
import pandas as pd
import re
import json

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import timedelta
from datetime import datetime

local_tz = pytz.timezone('Asia/Kuala_Lumpur')


def set_webdriver():

    # download in current folder path
    path = os.path.dirname(__file__)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-geolocation")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-browser-side-navigation")

    return webdriver.Chrome(ChromeDriverManager(path=path).install(), chrome_options=chrome_options)

def load_comments(driver):
    MAX_COMMENT = 2000
    
    for i in range(50):

        f = driver.find_elements_by_xpath('//*[contains(@id,"mount_0_0_")]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[2]/div/div[1]/div/div[2]/div/div/span')
        if f != []:
            break
    
    if f == []:

        return None

    else:

        pattern = re.compile(r'\d{0,2}\.?\d{0,2}')
        units = re.compile(r'[A-Z]')

        comments = float(re.search(pattern, f[0].text).group(0))

        try: 
            unit = re.search(units, f[0].text).group(0)

        except: 
            unit = re.search(units, f[0].text)


        cycle = 10
        if unit == 'K':
            comments *= 1000
            
            if MAX_COMMENT >= 2000:
                return True

        if comments > 50 and comments < 200:
            cycle = 3

        elif comments >= 200 and comments < 1000:
            cycle = 10

        elif comments > 1000:
            cycle = 15

        for i in range(cycle):
            
            lst = driver.find_elements_by_xpath('//*[contains(@id,"mount_0_0_")]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[4]/div[1]/div[1]/div[2]/span/span')
            try:
                for button in lst:
                    button.click()
            except:
                pass
    


def convert_time(x, now = datetime.now(tz=local_tz)):

    prefix, suffix = x[:-2], x[-1]

    d = int(prefix) if suffix == 'd' else 0
    h = int(prefix) if suffix == 'h' else 0
    m = int(prefix) if suffix == 'm' else 0
    s = int(prefix) if suffix == 's' else 0

    delta = timedelta(days=d, hours=h, minutes=m, seconds=s)

    return (now - delta).date()


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

    return new_df

        
        


def scrape_facebook(driver, HANDLE):
    ''' SOCIAL MEDIA WEB SCRAPER - FACEBOOK
    :param driver: chromedriver loaded using selenium
    :param HANDLE:
    :return df: compiled dataframe of user comments based on handle input
    login to account 
        1. login via main url
        2. search email, pass, login button
        3. send login details and submit for login
    '''

    f = open("scraping/logins.json")
    data = json.load(f)

    login_data = data['facebook']

    driver.get(login_data['url'])
    time.sleep(3)

    # enter username and password
    username = driver.find_element_by_name('email')
    password = driver.find_element_by_name('pass')
    submit = driver.find_element_by_name('login')

    username.clear()
    password.clear()
    username.send_keys(login_data['email'])
    password.send_keys(login_data['password'])

    submit.click()

    time.sleep(3)

    # begin scrape: look-up facebook posts by photos
    target_url = login_data['url'] + HANDLE + login_data['suffix']

    driver.get(target_url)
    time.sleep(5)

    # modify the value based on how many post links to extract
    # n_scrolls = random.randrange(5, 10, 1)
    n_scrolls = 3

    for j in range(1, n_scrolls):

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(random.randrange(3, 10, 1))

        anchors = driver.find_elements_by_tag_name('a')
        anchors = [a.get_attribute('href') for a in anchors]
        anchors = [a for a in anchors if str(a).startswith(target_url)]

    print(f'Number of links: {len(anchors)}')

    # unwrap data into dataframe format
    NOW = time.time()
    df = pd.DataFrame()

    for link in anchors:

        driver.get(link)
        driver.execute_script("window.scrollTo(0, document.body.ScrollHeight);")

        cont = load_comments(driver)  
        if cont:
            print('Exceeded limit, skipped post')
            continue

        x = random.randrange(3, 10, 1)
        time.sleep(x)

        # comment
        a = driver.find_elements_by_css_selector("div[class='kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql']")
        
        # commenter's username
        b = driver.find_elements_by_css_selector("span[class='d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa ht8s03o8 a8c37x1j keod5gw0 nxhoafnm aigsh9s9 fe6kdd0r mau55g9w c8b282yb d9wwppkn mdeji52x e9vueds3 j5wam9gi lrazzd5p oo9gr5id']")

        # time of comment
        c = driver.find_elements_by_css_selector("a.oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.m9osqain.gpro0wi8.knj5qynh span.tojvnm2t.a6sixzi8.abs2jz4q.a8s20v7p.t1p8iaqh.k5wvi7nf.q3lfd5jv.pk4s997a.bipmatt0.cebpdrjk.qowsmv63.owwhemhu.dp1hu0rb.dhp61c6y.iyyx5f41")
    

        lst = []
        for i,j,k in zip(a,b,c):
            # Time, Comment, Username
            lst.append([k.text, i.text, j.text])
        df = df.append(lst)


    df = df.rename({0:'Time',1:'Comment',2:'Username'},axis=1)
    df['Platform']  = 'FB'
    df = filter_comments(df)
    df['Time'] = df['Time'].apply(lambda x: convert_time(x)) # CHECK THIS 9/11

    END_TIME = time.time()
    print(f"Execution Time (hh:mm:ss.ms) {END_TIME-NOW}")

    return df


def main(HANDLE):

    driver = set_webdriver()
    df_fb = scrape_facebook(driver, HANDLE)
    driver.quit()
    print(df_fb)

    return df_fb
