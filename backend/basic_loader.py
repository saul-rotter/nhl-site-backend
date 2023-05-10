# type: ignore
import requests
import dropbox
import pandas as pd
from load_game_data import *
from database import Database
import numpy as np
import io
from sqlalchemy.dialects.sqlite import insert

database = Database()
database.init_no_app(True)
# Set up Dropbox API client
dbx = dropbox.Dropbox(
    "sl.BeAVhoG2I3SAa2-s7X9p33p6AXiEh_oFk-NQ8JMlNd_Xr49Q9Ygx8oI1CjvH9zY20XGWpzL7drF8k6Kgo-4sieRc_8AT5PNyt3OJdLESmg7cHZNVoBRFF__FRbgj0lkwEW-Rg6w")
# Set up NHL API endpoint and headers
nhl_endpoint = "https://statsapi.web.nhl.com/api/v1/game/{}/feed/live"
nhl_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Set up Dropbox API client
dbx = dropbox.Dropbox(
    "sl.BeHza3OzxeVPP1pljgQb-uIWmbjVOiRJlDdjRIT4mJb1vP1HEt_qMXwaVMxu3_5fxLB3r0NFFzJTjHTyINkXPMsoGVrMYwWDx05T6OIkTN6PmFbf_pc-t6NL6P8NWu8U61D7LjM"
)


def returnMatchRegex(x):
    match = re.search(r"\d+:\d+", str(x))
    if match:
        return match.group()
    else:
        return np.nan


def add_game_data(db, file):
    file_data = file.content
    df = pd.read_excel(io.BytesIO(file_data), dtype=str)
    df['Time'] = df['Time'].apply(returnMatchRegex)
    df["Period"] = df["Period"].apply(
        lambda x: x if str(x).isdigit() else np.nan)
    df["Period"] = df["Period"].fillna(method='ffill')
    df = df[df['Period'].notna()]
    df = df[df['Time'].notna()]

    # Extract game ID, home team, and away team from filename
    filename = entry.name
    game_id, _home_team, _away_team = filename.split(".")[0].split(" ")[0:3]
    full_game_id = f"{season}0{game_id}"
    # Get NHL data for game ID
    nhl_response = requests.get(
        nhl_endpoint.format(full_game_id), headers=nhl_headers)
    data = nhl_response.json()
    (teams_bp, players_bp) = fill_from_boxscore(
        data["liveData"]["boxscore"])
    awayTeamId = data["gameData"]["teams"]["away"]["id"]
    homeTeamId = data["gameData"]["teams"]["home"]["id"]
    game = fill_game_metadata(data)
    db.add(game)
    db.add_all(teams_bp)
    db.add_all(players_bp)
    events = fetch_or_initialize_pbp(
        data["liveData"]["plays"]["allPlays"],
        df,
        full_game_id,
        players_dict,
        teams_dict,
        homeTeamId,
        awayTeamId,
    )
    events.to_sql("events", database.engine,
                  if_exists="append", index=False)
    shifts = fetch_shifts(
        data["gameData"]["game"]["pk"]
    )
    db.add_all(shifts)


with database.session() as db:
    with db.begin():
        # Prompt user to choose between file or folder
        while True:
            choice = input("Enter 'file' or 'folder': ")
            if choice == "file":
                # Prompt user to enter file path
                file_path = input("Enter file path as 'season/filename': ")
                # Download file from Dropbox
                file = dbx.files_download(file_path)[1]
                add_game_data(db, file)
                break

            elif choice == "folder":
                # Prompt user to enter folder path
                season = input("Enter season: ")
                # List files in folder
                for entry in dbx.files_list_folder(f'/{season}').entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        # Download file from Dropbox
                        file = dbx.files_download(entry.path_display)[1]
                        add_game_data(db, file)
                break
