import pandas as pd
import requests
import time
import numpy as np
import itertools
from lxml import html
from lxml import etree
from bs4 import BeautifulSoup

def get_athletes():
    # url for this request
    url="http://powerof10.info/athletes/profile.aspx?athleteid=6004"

    # Scrape the HTML at the url
    r = requests.get(url)

    # Turn the HTML into a Beautiful Soup object
    soup = BeautifulSoup(r.text, 'lxml')
    
    div = soup.find("div", id ='cphBody_divBestPerformances')
    print ''.join(map(str, div.contents))
#    pass
#//*[@id="cphBody_divBestPerformances"]/table/tbody/tr[1]/td[1]/b
#//*[@id="cphBody_divBestPerformances"]/table/tbody/tr[2]/td[1]/b
#//*[@id="cphBody_divBestPerformances"]/table/tbody/tr[3]/td[4]

def get_coaches():
    pass

def get_clubs():
    pass

def get_results():    
    pass
   
def get_rankings(events, ages, sexes, years):
    """
    Return a dataframe of all results returned for a given combination of
    url parameters (events, ages, sexes, years)
    """

    # xpath patterns
    header_xpath = u'////tr[@class="rankinglistheadings"]//td'
    ranking_xpath = u'////*[@id="pnlMainRankings"]//table[1]//tr[(td[position() = 1 and normalize-space(.)!=""]) and (@class="rlr" or @class="rlra")]//td'
    athlete_xpath = ranking_xpath + '[7]//a[1]//@href'
    perfomance_xpath = ranking_xpath + '[14]//a[1]//@href'
    
    
    # url for power of 10
    protocol = "http://"
    domain = "www.thepowerof10.info"
    path = "/rankings/rankinglist.aspx"


    # construct a list containing every combination of parameters
    param_combos = list(itertools.product(events, ages, sexes, years))

    header_list = []
    ranking_list = []
    athlete_list = []
    performance_list = []
    num_headers = None
    
    all_ranking_lists = []
    all_athlete_lists = []
    all_performance_lists = []
    
    result_dfs = []

    # Iterate over the list of parameters
    for event, age_group, sex, year in param_combos:
        query = "?event=%s&agegroup=%s&sex=%s&year=%s" % (event, age_group, sex, year)
        rank_request_url = protocol + domain + path + query
        rank_page = requests.get(rank_request_url)
        tree = html.fromstring(rank_page.content)
        
        
        # Get the header on first request
        if not header_list:
            header_list = tree.xpath(header_xpath)
            header_list = [h.text_content().lower() for h in header_list]
            
            
            # Add in some missing headers
            header_list[2] = 'indoor'
            header_list[3] = 'wind'
            header_list[5] = 'pb_status'
            header_list[7] = 'age_group'
            header_list[-1] = 'performance_id'
            
            num_headers = len(header_list)

        ranking_list = [etree.tostring(elem, method='text', encoding='utf-8').strip()\
            for elem in tree.xpath(ranking_xpath)]
        athlete_list = [elem.split("=")[1] \
            for elem in tree.xpath(athlete_xpath)]
        performance_list = [elem.split("=")[1] \
            for elem in tree.xpath(perfomance_xpath)]


        
        assert len(ranking_list) / len(header_list) == len(athlete_list), \
            "mismatch between size of athlete and ranking list"
        
        
        # be nice and wait for a few seconds before making a second request
        time.sleep(5)

        # Could create and reshape at same time if I could figure out the 
        # correct reshape syntax.
        ranking_np = np.array(ranking_list)
        ranking_np.shape = (len(athlete_list), num_headers)
    
        df = pd.DataFrame(data=ranking_np, columns=header_list)
    
        df['rank'] = df['rank'].astype(int, raise_on_error=False)
        df['perf'] = df['perf'].astype(float, raise_on_error=False)
        df['wind'] = df['wind'].astype(float, raise_on_error=False)
        df['dob'] = pd.to_datetime(df['dob'], format='%d.%m.%y', errors='coerce')
        df['dop'] = pd.to_datetime(df['date'], format='%d %b %y', errors='coerce')
        df['event'] = event
        df['age_group2'] = age_group
        df['sex'] = sex
        df['year'] = year
        df['athlete_id'] = athlete_list
        df['performance_id'] = performance_list

        result_dfs.append(df)

    return pd.concat(result_dfs, ignore_index=True)

if __name__ == '__main__':
    get_athletes()
