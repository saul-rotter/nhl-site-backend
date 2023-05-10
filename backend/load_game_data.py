# type: ignore

import pandas as pd
import urllib.request
import json
from datetime import datetime, timedelta
import re
import requests
import load_a3z_data as load_a3z_data
from database.models import player, team, event, game, shift

players_dict = {}
teams_dict = {}


def utc_to_est(utc_dt):
    return utc_dt - timedelta(hours=5)


def convertTime(timeString, period):
    timeString = timeString.strip()
    time = 60 * int(timeString.split(":")[0]) + int(timeString.split(":")[1])
    return time + 20 * 60 * max(0, period - 1)


# pylint: disable=too-many-locals
def fetch_shifts(gameId):
    # https: // api.nhle.com/stats/rest/en/shiftcharts?cayenneExp = gameId = 2022020489
    response = requests.get(
        f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={gameId}"
    )
    shifts = response.json()
    shifts_list = []
    for shift_obj in shifts['data']:
        shift_obj['shiftStart'] = convertTime(
            shift_obj['startTime'], shift_obj['period']
        )
        shift_obj['shiftEnd'] = convertTime(
            shift_obj['endTime'], shift_obj['period']
        )
        shifts_list.append(
            shift.Shift(
                gameId=int(shift_obj['gameId']),
                playerId=int(shift_obj['playerId']),
                teamId=int(shift_obj['teamId']),
                shiftStart=int(shift_obj['shiftStart']),
                shiftEnd=int(shift_obj['shiftEnd'])
            )
        )
    return shifts_list


def fill_players_from_boxscore(player_data, team_id):
    players = []
    for player_dict in player_data.values():
        players.append(
            player.Player(
                id=player_dict["person"]["id"],
                name=player_dict["person"]["fullName"],
                number=player_dict["jerseyNumber"],
                teamId=team_id,
                position=player_dict["position"]["code"],
                hand=player_dict["person"]["shootsCatches"],
            )
        )
        players_dict[(team_id, player_dict["jerseyNumber"])] = player_dict["person"][
            "id"
        ]
    return players


def fill_game_metadata(data):
    gameId = data["gameData"]["game"]["pk"]
    season = data["gameData"]["game"]["season"]
    startTime = utc_to_est(
        datetime.fromisoformat(data["gameData"]["datetime"]["dateTime"][:-1])
    ).strftime("%m/%d/%Y, %H:%M:%S")
    awayTeamId = data["gameData"]["teams"]["away"]["id"]
    homeTeamId = data["gameData"]["teams"]["home"]["id"]
    homeScore = data["liveData"]["boxscore"]["teams"]["home"]["teamStats"][
        "teamSkaterStats"
    ]["goals"]
    awayScore = data["liveData"]["boxscore"]["teams"]["away"]["teamStats"][
        "teamSkaterStats"
    ]["goals"]
    homeCoach = data["liveData"]["boxscore"]["teams"]["home"]["coaches"][0]["person"][
        "fullName"
    ]
    awayCoach = data["liveData"]["boxscore"]["teams"]["away"]["coaches"][0]["person"][
        "fullName"
    ]
    return game.Game(
        id=gameId,
        season=season,
        startTime=startTime,
        homeTeamId=homeTeamId,
        homeCoach=homeCoach,
        homeScore=homeScore,
        awayTeamId=awayTeamId,
        awayCoach=awayCoach,
        awayScore=awayScore,
    )


def deleteLeadingZeros(inputString):
    # regex pattern for removing leading zeros from an input string
    regexPattern = "^0(?!$)"
    # Replace the matched regex pattern with an empty string
    outputString = re.sub(regexPattern, "", inputString)
    # returning output
    return outputString


def fetch_or_initialize_pbp(pbp, df, gameId, players_dict, teams_dict, homeTeamId, awayTeamId,):
    period = [None for i in range(len(pbp))]
    time = ["0:00" for i in range(len(pbp))]
    dateTime = [None for i in range(len(pbp))]
    event = ["NA" for i in range(len(pbp))]
    event_type = [None for i in range(len(pbp))]
    team = [None for i in range(len(pbp))]
    p1 = [None for i in range(len(pbp))]
    p2 = [None for i in range(len(pbp))]
    awayGoals = [None for i in range(len(pbp))]
    homeGoals = [None for i in range(len(pbp))]

    for i in range(len(pbp)):
        period[i] = int(pbp[i]["about"]["period"])
        time[i] = pbp[i]["about"]["periodTimeRemaining"]
        awayGoals[i] = int(pbp[i]["about"]["goals"]["away"])
        homeGoals[i] = int(pbp[i]["about"]["goals"]["home"])

        dateTime[i] = utc_to_est(  # type: ignore
            datetime.fromisoformat(pbp[i]["about"]["dateTime"][:-1])
        ).strftime("%m/%d/%Y, %H:%M:%S")
        event[i] = pbp[i]["result"]["event"]
        if event[i] == 'Blocked Shot':
            event[i] = 'Missed Shot'
            team[i] = awayTeamId if pbp[i]["team"]["id"] == homeTeamId else homeTeamId
            p1[i] = pbp[i]["players"][1]["player"]["id"]
            p2[i] = pbp[i]["players"][0]["player"]["id"]
            # Do the action
        try:
            team[i] = pbp[i]["team"]["id"]
        except KeyError:
            pass
        try:
            p1[i] = pbp[i]["players"][0]["player"]["id"]
        except KeyError:
            pass
        try:
            event_type[i] = pbp[i]["result"]["secondaryType"]
        except KeyError:
            pass
        try:
            if event[i] == 'Goal':
                continue
            p2[i] = pbp[i]["players"][1]["player"]["id"]
        except KeyError:
            pass
        except IndexError:  # e.g. on a give or take
            pass
    pbpdf = pd.DataFrame(
        {
            "period": period,
            "time": time,
            "dateTime": dateTime,
            "event": event,
            "team": team,
            "player": p1,
            "oppPlayer": p2,
            "type": event_type,
            "homeScore": homeGoals,
            "awayScore": awayGoals
        },
    )
    # pbpdf.drop(pbpdf[pbpdf["team"] == ""].index, inplace=True)
    # pbpdf["datetime_shifted"] = pbpdf["dateTime"].shift(1)
    # pbpdf["datetime_shifted"].iloc[0] = start_time
    # pbpdf["time_since_last_event"] = (pbpdf.dateTime - pbpdf.datetime_shifted).apply(
    #     lambda x: x.total_seconds()
    # )
    pbpdf["time"] = pbpdf["time"].astype(str).apply(deleteLeadingZeros)

    def convert_game_time(period, time):
        time_list = time.split(":")
        clock = (int(time_list[0]) * 60) + (int(time_list[1]))
        return int(period * 1200 - clock)

    pbpdf["seconds"] = pbpdf.apply(
        lambda x: convert_game_time(x["period"], x["time"]), axis=1
    )
    # pbpdf.drop(["period", "time"], axis=1, inplace=True)
    # pbpdf.set_index("seconds", inplace=True, drop=False)
    a3z_pbp = load_a3z_data.get_clean_a3z_game_data(
        df, players_dict, teams_dict)
    merged_df = (
        pd.merge(
            pbpdf,
            a3z_pbp,
            on=["seconds", "event", "team", "player", "period", "time"],
            how="outer",
        )
    ).sort_values("seconds")
    merged_df["oppPlayer"] = merged_df[["oppPlayer_x", "oppPlayer_y"]].apply(
        lambda x: x["oppPlayer_y"] if pd.isna(
            x["oppPlayer_x"]) else x["oppPlayer_x"],
        axis=1,
    )
    merged_df.drop(["oppPlayer_x", "oppPlayer_y"], axis=1, inplace=True)
    merged_df["oppTeam"] = merged_df["team"].apply(
        lambda x: awayTeamId if x == homeTeamId else homeTeamId
    )
    merged_df["type"] = merged_df[["type_x", "type_y"]].apply(
        lambda x: x["type_y"] if pd.isna(
            x["type_x"]) else x["type_x"],
        axis=1,
    )
    merged_df.drop(["type_x", "type_y"], axis=1, inplace=True)
    merged_df["gameId"] = gameId
    merged_df["homeScore"] = merged_df["homeScore"].fillna(method='ffill')
    merged_df["awayScore"] = merged_df["awayScore"].fillna(method='ffill')
    return merged_df.rename(columns={
        'team': 'teamId',
        'oppTeam': 'oppTeamId',
        'player': 'playerId',
        'oppPlayer': 'oppPlayerId',
        'oppTeam': 'oppTeamId',
        'recovery': 'recoveryId',
        'retrieval': 'retrievalId',
        'primaryAssist': 'primaryAssistId',
        'secondaryAssist': 'secondaryAssistId',
        'tertiaryAssist': 'tertiaryAssistId',
    })


def fetch_game_from_nhl_api(gameId):
    with urllib.request.urlopen(
        f"https://statsapi.web.nhl.com/api/v1/game/{gameId}/feed/live"
    ) as reader:
        game_page = reader.read()

    game = json.loads(game_page.decode("latin-1"))
    return game


def fill_from_boxscore(boxscore):
    players = []
    teams = []
    for team_boxscore in boxscore["teams"].values():
        teams.append(
            team.Team(
                id=team_boxscore["team"]["id"],
                abbrev=team_boxscore["team"]["triCode"],
                name=team_boxscore["team"]["name"],
            )
        )
        teams_dict[team_boxscore["team"]["triCode"]
                   ] = team_boxscore["team"]["id"]
        teams_dict[team_boxscore["team"]
                   ["name"].lower()] = team_boxscore["team"]["id"]
        players.extend(
            fill_players_from_boxscore(
                team_boxscore["players"], team_boxscore["team"]["id"]
            )
        )
    return (teams, players)
