from functools import cache
import pandas as pd

moneypuck_shots_endpoint = "https://peter-tanner.com/moneypuck/downloads/shots_{season}.zip"
@cache
def download_shots_data(season):
  url = moneypuck_shots_endpoint.format(season=season)
  shots_df = pd.read_csv(url, compression='zip', storage_options = {'User-Agent': 'Mozilla/9.0'})
  return shots_df

@cache
def get_game_data(season, game_id):
  shots_df = download_shots_data(season)
  game_shots = shots_df[shots_df['game_id'] == int(game_id)][['game_id', 'time', 'period', 'team', 'event', 'goal', 'xGoal', 'arenaAdjustedXCord', 'arenaAdjustedYCord']]
  game_shots["seconds"] = game_shots['time']
  return game_shots