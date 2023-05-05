from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from nhl_game_scraper import get_nhl_game_events
from a3z_scraper import get_a3z_game_data
import re

# Make sure it works when first video link is removed
def get_video_url(team1, team2, date1):
    s = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=s, options=options)
    driver.get(f"https://nhlvideo.net/{team1}-vs-{team2}-full-game-replay-{date1}-nhl")
    soup = BeautifulSoup(driver.page_source, "html.parser")

    return soup.find_all("iframe")[1].attrs["src"][2:]


def merge_a3z_and_nhl():
    a3z_pbp = get_a3z_game_data()
    nhl_pbp_data = get_nhl_game_events(2022020489)
    # f"{video_url}?fromTime={buffer}"
    merged_df = (
        a3z_pbp.merge(nhl_pbp_data, on=["Seconds", "Team"], how="outer")
        .sort_values("Seconds")
        .reset_index()
    )
    merged_df.loc[
        merged_df[
            (merged_df["Event"].isna()) & (~(merged_df["Entry Type"].isna()))
        ].index,
        "Event",
    ] = "Zone Entry"
    merged_df.loc[
        merged_df[
            (merged_df["Event"].isna()) & (~(merged_df["Retrieval"].isna()))
        ].index,
        "Event",
    ] = "Puck Retrieval"

    # Get team for Zone Entry from Entry By (get non_numeric)
    # Get team for Retrieval from Retrival (get non numeric)
    zone_entry_index = merged_df[merged_df["Event"] == "Zone Entry"].index
    retrieval_index = merged_df[merged_df["Event"] == "Puck Retrieval"].index
    merged_df.loc[zone_entry_index, "Team"] = merged_df.loc[
        zone_entry_index, "Entry By"
    ].apply(lambda x: re.sub(r"[^A-Za-z]+", "", x))
    merged_df.loc[retrieval_index, "Team"] = merged_df.loc[
        retrieval_index, "Retrieval"
    ].apply(lambda x: re.sub(r"[^A-Za-z]+", "", x))
    return merged_df[
        [
            "Team",
            "Event",
            "Seconds",
            "Period_x",
            "Time_x",
            "Period_y",
            "Time_y",
            "DateTime",
            "time_since_last_event",
        ]
    ]


# Filter df for seconds, event, team. This will be the first set we will work with
# if necessary create API, but shouldn't be necessary

video_url = get_video_url("new-york-rangers", "philadelphia-flyers", "dec-17-2022")

# Buffer may be necessary for certain games, but on site will be added manually
start_buffer = 346
df = merge_a3z_and_nhl()
df.drop(df[df["Team"] == ""].index, inplace=True)
print(df.head(20))
#  Period Start - Prev Period End from nhl pbp  period_buffer = 900
# print(f"{video_url}?fromTime={a + start_buffer}")
# event = Zone Entry: merged_df[(data['Event'].isna()) & (~(data['Entry Type'].isna()))]
# event = Puck Retrieval: merged_df[(data['Event'].isna()) & (~(data['Retrieval'].isna()))]
