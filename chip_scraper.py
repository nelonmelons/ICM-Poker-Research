import requests
from bs4 import BeautifulSoup
import csv

def scrape_chipcounts(urls, output_csv):
    all_rows = []
    headers = ['Rank', 'Name', 'Chip Count', 'Trend']

    for url in urls:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        soup = BeautifulSoup(response.text, "html.parser")
        chipcounts_div = soup.find("div", id="chipcounts")

        if not chipcounts_div:
            print("Could not find the 'chipcounts' div on the page.")
            exit()
            
        ul_tag = chipcounts_div.find("ul")
        if not ul_tag:
            print("Could not find the <ul> inside 'chipcounts' div.")
            exit()
        li_list = ul_tag.find_all("li")
        data_lis = li_list[7:] #skip headers
        step = 7
        for i in range(0, len(data_lis), step):
            chunk = data_lis[i:i+step]
            # Ensure we actually have 7 items in this chunk
            if len(chunk) < 7:
                break
            rank      = chunk[0].get_text(strip=True)
            player     = chunk[1].get_text(strip=True)
            chip_count = chunk[2].get_text(strip=True)
            trend      = chunk[3].get_text(strip=True)

            all_rows.append([rank, player, chip_count, trend])

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)

urls_to_scrape = [
    "https://www.wsop.com/tournaments/chipcounts/?aid=1&grid=5648&tid=24164&dayof=241644&rr=-1",
    # add more URLs if needed
]
scrape_chipcounts(urls_to_scrape, "combined_chips.csv")
