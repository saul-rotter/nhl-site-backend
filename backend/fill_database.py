# type: ignore
import numpy as np
import dropbox
import pandas as pd
from load_nhl_data import NHLGameFeed
from database import Database
from load_a3z_data import get_clean_a3z_game_data
from database.models import player, team, event, game, shift
import argparse
from moneypuck import get_game_data
pd.options.mode.chained_assignment = None  # default='warn'
parser = argparse.ArgumentParser(
    prog="FillNHLDatabase",
    description="Pulls data from nhl API and dropbox to fill the API for the nhl play app",
)
parser.add_argument(
    "-b",
    "--backfill",
    action="store_true",
    dest="backfill",
    help="If true, will reset the entire database and start from scratch. Otherwise, it will only add new data",
)
parser.add_argument(
    "-d",
    "--dry_run",
    action="store_true",
    dest="dry_run",
    help="If true it will not write to the database",
)

args = parser.parse_args()

# Set up Dropbox API client
dbx = dropbox.Dropbox(
    "sl.BnUCImc6H7L2KZPWEV7uG2eIcm8xyXf5dKQlppSfUrm6S0XPgzGEhN1_GXHmxly51RwZCn4JKLp7QTqC1G02qt0Bc8SKxWR9bk1F7MB-3WC4jUQshO-yHMi2w2oORdWa3A1HAXyfUdDD"
)


def add_game_data(file, games, teams, players, events, shifts):
    file_data = file.content
    # Extract game ID, home team, and away team from filename
    filename = entry.name
    game_id, _home_team, _away_team = filename.split(".")[0].split(" ")[0:3]
    full_game_id = f"{season}0{game_id}"
    nhl_api = NHLGameFeed(full_game_id)
    nhl_api.initialize_data()
    a3z_pbp = get_clean_a3z_game_data(
        file_data, nhl_api.players_dict, nhl_api.teams_dict
    )
    
    merged_pbp = nhl_api.merge_with_a3z(a3z_pbp)
    mp_data = get_game_data(season,game_id)
    merged_pbp= pd.merge(merged_pbp,mp_data[['seconds', 'xGoal', 'arenaAdjustedXCord', 'arenaAdjustedYCord']], on='seconds',how='outer')
    games = games + [nhl_api.game]
    teams = teams + nhl_api.teams
    players = players + nhl_api.players
    events.append(merged_pbp)
    shifts = shifts + nhl_api.shifts
    return (games, players, teams, events, shifts)


events = []
games = []
players = []
teams = []
shifts = []

while True:
    choice = input("Enter 'file' or 'folder': ")
    if choice == "file":
        # Prompt user to enter file path
        file_path = input("Enter file path as 'season/filename': ")
        # Download file from Dropbox
        file = dbx.files_download(file_path)[1]
        (games, players, teams, events, shifts) = add_game_data(
            file, games, teams, players, events, shifts
        )
        break

    elif choice == "folder":
        # Prompt user to enter folder path
        season = input("Enter season: ")
        # List files in folder
        for entry in dbx.files_list_folder(f"/{season}").entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                # Download file from Dropbox
                file = dbx.files_download(entry.path_display)[1]
                (games, players, teams, events, shifts) = add_game_data(
                    file, games, teams, players, events, shifts
                )
        break
print(pd.concat(events).columns)
if not args.dry_run:
    database = Database()
    database.init_no_app(args.backfill)
    with database.session() as db:
        with db.begin():
            if not args.dry_run:
                db.execute(Database.upsert(team.Team, teams))
                db.execute(Database.upsert(player.Player, players))
                db.execute(Database.upsert(game.Game, games))
                db.execute(Database.upsert(shift.Shift, shifts))
                db.commit()
                db.close()
        event_df = pd.concat(events).drop_duplicates()
        event_df.replace("", np.NaN, inplace=True)
        # print(event_df['recoveryId'].unique())
        event_df.to_sql("events", database.engine, if_exists="append", index=False)
