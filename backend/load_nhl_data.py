# type: ignore

import pandas as pd
from datetime import datetime, timedelta
import re
import requests

nhl_endpoint = "https://statsapi.web.nhl.com/api/v1/game/{}/feed/live"


def utc_to_est(utc_dt):
    return utc_dt - timedelta(hours=5)


def convertTime(timeString, period):
    timeString = timeString.strip()
    time = 60 * int(timeString.split(":")[0]) + int(timeString.split(":")[1])
    return time + 20 * 60 * max(0, period - 1)


def deleteLeadingZeros(inputString):
    # regex pattern for removing leading zeros from an input string
    regexPattern = "^0(?!$)"
    # Replace the matched regex pattern with an empty string
    outputString = re.sub(regexPattern, "", inputString)
    # returning output
    return outputString


class NHLGameFeed:
    def __init__(self, gameId) -> None:
        self.gameId = gameId
        nhl_response = requests.get(nhl_endpoint.format(gameId))
        self.api_data = nhl_response.json()
        self.shifts = []
        self.pbp = []
        self.players = []
        self.teams = []
        self.game = {}
        self.players_dict = {}
        self.teams_dict = {}

    def initialize_data(self):
        (self.teams, self.players) = self._fill_from_boxscore()
        self.game = self._fill_game_metadata()
        self.pbp = self._fill_pbp()
        self.shifts = self._fill_shifts()

    def _fill_shifts(self):
        # https: // api.nhle.com/stats/rest/en/shiftcharts?cayenneExp = gameId = 2022020489
        response = requests.get(
            f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={self.gameId}"
        )
        shifts = response.json()
        shifts_list = []
        for shift_obj in shifts["data"]:
            shift_obj["shiftStart"] = convertTime(
                shift_obj["startTime"], shift_obj["period"]
            )
            shift_obj["shiftEnd"] = convertTime(
                shift_obj["endTime"], shift_obj["period"]
            )
            shifts_list.append(
                {
                    "gameId": int(shift_obj["gameId"]),
                    "playerId": int(shift_obj["playerId"]),
                    "teamId": int(shift_obj["teamId"]),
                    "shiftStart": int(shift_obj["shiftStart"]),
                    "shiftEnd": int(shift_obj["shiftEnd"]),
                }
            )
        return shifts_list

    def _fill_players_from_boxscore(self, player_data, team_id):
        players = []
        for player_dict in player_data.values():
            players.append(
                {
                    "id": player_dict["person"]["id"],
                    "name": player_dict["person"]["fullName"],
                    "number": player_dict["jerseyNumber"],
                    "teamId": team_id,
                    "position": player_dict["position"]["code"],
                    "hand": player_dict["person"]["shootsCatches"],
                }
            )
            self.players_dict[(team_id, int(player_dict["jerseyNumber"]))] = int(
                player_dict["person"]["id"]
            )
        return players

    def _fill_game_metadata(self):
        gameId = self.api_data["gameData"]["game"]["pk"]
        season = self.api_data["gameData"]["game"]["season"]
        startTime = utc_to_est(
            datetime.fromisoformat(
                self.api_data["gameData"]["datetime"]["dateTime"][:-1]
            )
        ).strftime("%m/%d/%Y, %H:%M:%S")
        awayTeamId = self.api_data["gameData"]["teams"]["away"]["id"]
        homeTeamId = self.api_data["gameData"]["teams"]["home"]["id"]
        homeScore = self.api_data["liveData"]["boxscore"]["teams"]["home"]["teamStats"][
            "teamSkaterStats"
        ]["goals"]
        awayScore = self.api_data["liveData"]["boxscore"]["teams"]["away"]["teamStats"][
            "teamSkaterStats"
        ]["goals"]
        homeCoach = self.api_data["liveData"]["boxscore"]["teams"]["home"]["coaches"][
            0
        ]["person"]["fullName"]
        awayCoach = self.api_data["liveData"]["boxscore"]["teams"]["away"]["coaches"][
            0
        ]["person"]["fullName"]
        return {
            "id": gameId,
            "season": season,
            "startTime": startTime,
            "homeTeamId": homeTeamId,
            "homeCoach": homeCoach,
            "homeScore": homeScore,
            "awayTeamId": awayTeamId,
            "awayCoach": awayCoach,
            "awayScore": awayScore,
        }

    def _fill_pbp(self):
        pbp = self.api_data["liveData"]["plays"]["allPlays"]
        awayTeamId = self.api_data["gameData"]["teams"]["away"]["id"]
        homeTeamId = self.api_data["gameData"]["teams"]["home"]["id"]
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
        result = [None for i in range(len(pbp))]

        for i in range(len(pbp)):
            period[i] = int(pbp[i]["about"]["period"])
            time[i] = pbp[i]["about"]["periodTimeRemaining"]
            awayGoals[i] = int(pbp[i]["about"]["goals"]["away"])
            homeGoals[i] = int(pbp[i]["about"]["goals"]["home"])

            dateTime[i] = utc_to_est(  # type: ignore
                datetime.fromisoformat(pbp[i]["about"]["dateTime"][:-1])
            ).strftime("%m/%d/%Y, %H:%M:%S")
            event[i] = pbp[i]["result"]["event"]
            if event[i] == "Blocked Shot":
                event[i] = "Shot"
                result[i] = "Blocked"
                team[i] = (
                    awayTeamId if pbp[i]["team"]["id"] == homeTeamId else homeTeamId
                )
                p1[i] = int(pbp[i]["players"][0]["player"]["id"])
                p2[i] = int(pbp[i]["players"][1]["player"]["id"])
                # Do the action
            elif event[i] == "Missed Shot":
                event[i] = "Shot"
                result[i] = "Missed"
            elif event[i] == "Goal":
                event[i] = "Shot"
                result[i] = "Goal"
            elif event[i] == "Shot":
                result[i] = "On Goal"
            try:
                team[i] = pbp[i]["team"]["id"]
            except KeyError:
                pass
            try:
                p1[i] = int(pbp[i]["players"][0]["player"]["id"])
            except KeyError:
                pass
            try:
                event_type[i] = pbp[i]["result"]["secondaryType"]
            except KeyError:
                pass
            try:
                p2[i] = int(pbp[i]["players"][1]["player"]["id"])
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
                "awayScore": awayGoals,
                "result": result,
            },
        )
        # pbpdf.drop(pbpdf[pbpdf["team"] == ""].index, inplace=True)
        # pbpdf["datetime_shifted"] = pbpdf["dateTime"].shift(1)
        # pbpdf["datetime_shifted"].iloc[0] = start_time
        # pbpdf["time_since_last_event"] = (pbpdf.dateTime - pbpdf.datetime_shifted).apply(
        #     lambda x: x.total_seconds()
        # )
        pbpdf["num_time"] = pbpdf["time"].astype(str).apply(deleteLeadingZeros)

        def convert_game_time(period, time):
            time_list = time.split(":")
            clock = (int(time_list[0]) * 60) + (int(time_list[1]))
            return int(period * 1200 - clock)

        pbpdf["seconds"] = pbpdf.apply(
            lambda x: convert_game_time(x["period"], x["num_time"]), axis=1
        )
        # pbpdf.drop(["period", "time"], axis=1, inplace=True)
        # pbpdf.set_index("seconds", inplace=True, drop=False)
        return pbpdf

    def _fill_from_boxscore(self):
        players = []
        teams = []
        boxscore = self.api_data["liveData"]["boxscore"]
        for team_boxscore in boxscore["teams"].values():
            teams.append(
                {
                    "id": team_boxscore["team"]["id"],
                    "abbrev": team_boxscore["team"]["triCode"],
                    "name": team_boxscore["team"]["name"],
                }
            )
            self.teams_dict[team_boxscore["team"]["triCode"]] = team_boxscore["team"][
                "id"
            ]
            self.teams_dict[team_boxscore["team"]["name"].lower()] = team_boxscore[
                "team"
            ]["id"]
            players.extend(
                self._fill_players_from_boxscore(
                    team_boxscore["players"], team_boxscore["team"]["id"]
                )
            )
        return (teams, players)

    def merge_with_a3z(self, a3z_pbp):
        awayTeamId = self.api_data["gameData"]["teams"]["away"]["id"]
        homeTeamId = self.api_data["gameData"]["teams"]["home"]["id"]
        merged_df = (
            pd.merge(
                self.pbp,
                a3z_pbp,
                on=["seconds", "event", "team", "player", "period", "time"],
                how="outer",
            )
        ).sort_values("seconds")
        merged_df["oppPlayer"] = merged_df[["oppPlayer_x", "oppPlayer_y"]].apply(
            lambda x: x["oppPlayer_y"]
            if pd.isna(x["oppPlayer_x"])
            else x["oppPlayer_x"],
            axis=1,
        )
        merged_df.drop(["oppPlayer_x", "oppPlayer_y"], axis=1, inplace=True)
        merged_df["oppTeam"] = merged_df["team"].apply(
            lambda x: awayTeamId if x == homeTeamId else homeTeamId
        )
        merged_df["type"] = merged_df[["type_x", "type_y"]].apply(
            lambda x: x["type_y"] if pd.isna(x["type_x"]) else x["type_x"],
            axis=1,
        )
        merged_df.drop(["type_x", "type_y"], axis=1, inplace=True)
        merged_df["gameId"] = self.gameId
        merged_df["homeScore"] = merged_df["homeScore"].fillna(method="ffill")
        merged_df["awayScore"] = merged_df["awayScore"].fillna(method="ffill")
        
        merged_df.rename(
            columns={
                "team": "teamId",
                "oppTeam": "oppTeamId",
                "player": "playerId",
                "oppPlayer": "oppPlayerId",
                "oppTeam": "oppTeamId",
                "recovery": "recoveryId",
                "retrieval": "retrievalId",
                "primaryAssist": "primaryAssistId",
                "secondaryAssist": "secondaryAssistId",
                "tertiaryAssist": "tertiaryAssistId",
            },
            inplace=True
        )

        assist_columns = ['chance', 'lane', 'primaryAssistId', 'secondaryAssistId', 'tertiaryAssistId','playType', 'oddman',
        'primaryZone', 'secondaryZone', 'tertiaryZone', 'primaryLane',
        'secondaryLane', 'tertiaryLane', 'primaryPassType', 'secondaryPassType',
        'tertiaryPassType', 'type']
        shots = merged_df[merged_df['event'] == 'Shot']
        shots['time_diff'] = shots['seconds'].diff()
        prev_index = -1
        for index, row in shots.iterrows():
            if (row['time_diff'] <= 1):
                merged_df.loc[prev_index, assist_columns] = row[assist_columns]
            prev_index = index
        return merged_df.drop(shots[(shots['time_diff'] <= 1)].index)
        
