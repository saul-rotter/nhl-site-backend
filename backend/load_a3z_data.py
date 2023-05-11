import io
import re
import numpy as np
import pandas as pd


def returnMatchRegex(x):
    match = re.search(r"\d+:\d+", str(x))
    if match:
        return match.group()
    else:
        return np.nan


def convert_game_time(index, period, time):
    if (time == '1900-01-04 13:13:00'):
        print(index)

    time_list = time.split(":")
    clock = (int(time_list[0]) * 60) + (int(time_list[1]))
    return int(period) * 1200 - clock


def read_a3z_game_data(file_data):
    df = pd.read_excel(io.BytesIO(file_data), dtype=str)
    df['Time'] = df['Time'].apply(returnMatchRegex)
    df["Period"] = df["Period"].apply(
        lambda x: x if str(x).isdigit() else np.nan)
    df["Period"] = df["Period"].fillna(method='ffill')
    df = df[df['Period'].notna()]
    df = df[df['Time'].notna()]
    df = df.drop(["Home", "Road", "Date"], axis=1)
    columns = list(df.drop("Period", axis=1).columns)
    df.dropna(how="all", inplace=True, subset=columns)

    df.rename(
        columns={"Period": "period", "Time": "time"},
        inplace=True,
    )
    df["seconds"] = df.apply(
        lambda x: convert_game_time(x, x["period"], x["time"]), axis=1
    )
    return df.sort_values("seconds").reset_index(drop=True)


def clean_zone_entries(zone_entries):
    zone_entries = zone_entries.dropna(
        subset=list(zone_entries.columns[3:]), how="all")
    zone_entries = zone_entries.drop(
        zone_entries[zone_entries["Entry Type"] == "X"].index
    )
    zone_entries["team"] = zone_entries["Entry By"].apply(
        lambda x: "".join(list(filter(str.isalpha, x)))
    )
    zone_entries["player"] = zone_entries["Entry By"].apply(
        lambda x: "".join(list(filter(str.isdigit, x)))
    )
    zone_entries["oppTeam"] = zone_entries["Defended by"].apply(
        lambda x: "".join(list(filter(str.isalpha, x)))
    )
    zone_entries["oppPlayer"] = zone_entries["Defended by"].apply(
        lambda x: "".join(list(filter(str.isdigit, x)))
    )
    zone_entries["recovery"] = zone_entries["Dump recovered?"].apply(
        lambda x: "".join(list(filter(str.isdigit, x)))
    )
    zone_entries["event"] = "Zone Entry"

    entry_type = {
        "D": "Dump",
        "C": "Carry",
        "F": "Failed Entry",
    }
    zone_entries["type"] = zone_entries[["Entry Type", "Pass?"]].apply(
        lambda x: entry_type[x["Entry Type"]]
        if not (entry_type[x["Entry Type"]] and x["Pass?"] == "Y")
        else "CARRIED_WITH_PASS",
        axis=1,
    )
    zone_entries.rename(
        columns={"Chance?": "chance", "Lane": "lane"}, inplace=True)
    # CARRIED WITH PASS (where pass is Y)
    return zone_entries[
        [
            "period",
            "time",
            "event",
            "type",
            "team",
            "player",
            "oppTeam",
            "oppPlayer",
            "lane",
            "recovery",
            "chance",
        ]
    ]


# ZONE EXIT
def clean_zone_exits(zone_exits):
    zone_exits = zone_exits.dropna(
        subset=list(zone_exits.columns[3:]), how="all")
    zone_exits.fillna("N", inplace=True)
    zone_exits.head()
    zone_exits["team"] = zone_exits["Retrieval"].apply(
        lambda x: "".join(list(filter(str.isalpha, x)))
    )
    zone_exits["player"] = zone_exits[["Retrieval", "Exit"]].apply(
        lambda x: "".join(list(filter(str.isdigit, x["Retrieval"])))
        if x["Exit"] == "N"
        else "".join(list(filter(str.isdigit, x["Exit"]))),
        axis=1,
    )
    zone_exits["retrieval"] = zone_exits[["Retrieval", "Exit"]].apply(
        lambda x: "".join(list(filter(str.isdigit, x["Retrieval"])))
        if x["Exit"] != "N"
        else "N",
        axis=1,
    )
    zone_exits["oppTeam"] = zone_exits["Pressure"].apply(
        lambda x: "".join(list(filter(str.isalpha, x)))
    )
    zone_exits["oppPlayer"] = zone_exits["Pressure"].apply(
        lambda x: "".join(list(filter(str.isdigit, x)))
    )
    zone_exits["event"] = "Zone Exit"
    # shots[['SOG?', 'G?']].apply(lambda x: 'Goal' if x['G?'] == 'y' else (('Shot' if x['SOG?'] == 'y' else 'Missed Shot')), axis=1)
    exit_types = {
        "BOT": "Botched Retrieval",
        "FEX": "Failed Exit",
        "PEX": "Passed",
        "MEX": "Missed Pass",
        "CEX": "Carried",
        "CLE": "Clear",
        "I": "Icing",
    }
    zone_exits["type"] = zone_exits[["Result", "Result.1"]].apply(
        lambda x: exit_types[x["Result"]]
        if x["Result"] != "EXC"
        else (
            exit_types[x["Result.1"]
                       ] if x["Result.1"] != "N" else "Botched Retrieval"
        ),
        axis=1,
    )
    # Switch exit and Retrieval Number
    # 'Period', 'Time', 'Strength', 'Event', 'Type', 'Team', 'Number', 'dTeam', 'dNumber', 'Recovery'
    return zone_exits[
        [
            "period",
            "time",
            "event",
            "type",
            "team",
            "player",
            "oppTeam",
            "oppPlayer",
            "retrieval",
        ]
    ]


def clean_shots(shots):
    # SHOT TABLE SPLIT FOR PASSES MANIPULATIONS
    pass_types = {
        "p": "Low-To-High",
        "s": "Stretch",
        "f": "Faceoff",
        "rr": "Slot",
        "el": "Below-Goal-Line",
    }

    zones = {
        "o": "Offensive",
        "d": "Defensive",
        "n": "Neutral",
        "oz": "Offensive",
        "dz": "Defensive",
        "nz": "Neutral",
    }

    lanes = {
        "l": "left",
        "r": "right",
        "c": "center",
        "L": "left",
        "R": "right",
        "C": "center",
    }

    shot_types = {
        "a": "Wrap Around",
        "b": "Backhander",
        "s": "Slapshot",
        "w": "Wrist Shot",
        "o": "One Timer",
        "r": "Rebound",
        "t": "Tip",
    }
    play_types = {
        "f": "Forecheck",
        "r": "Rush",
        "c": "Cycle",
    }
    shots = shots.dropna(subset=list(shots.columns[3:]), how="all")
    shots[["Shooter", "A1", "A2", "A3"]] = (
        (shots[["Shooter", "A1", "A2", "A3"]].fillna(-1))
        .astype("int")
        .astype("str")
        .replace("-1", None)
    )
    shots["event"] = shots[["SOG?", "G?"]].apply(
        lambda x: "Goal"
        if x["G?"] == "y"
        else (("Shot" if x["SOG?"] == "y" else "Missed Shot")),
        axis=1,
    )
    # Period Time Strength Event Type Team Number primaryAssist secondaryAssist tertiaryAssist Chance playType oddMan screened origin
    #             primaryZone primaryLane primaryPassType secondaryZone secondaryLane secondaryPassType tertiaryZone tertiaryLane tertiaryPassType
    shots["primaryZone"] = shots["A1 Zone"].apply(
        lambda x: zones[str(x)[0]] if (
            str(x) != "nan") and (str(x)[0] in zones) else ""
    )
    shots["primaryLane"] = shots["A1 Zone"].apply(
        lambda x: lanes[str(x)[-1]] if str(x)[-1] in lanes else ""
    )
    shots["primaryPassType"] = shots["A1 Zone"].apply(
        lambda x: pass_types[str(x)[1:-1]] if str(x)[1:-
                                                     1] in pass_types else ""
    )
    shots["secondaryZone"] = shots["A2 Zone"].apply(
        lambda x: zones[str(x)[0]] if (
            str(x) != "nan") and (str(x)[0] in zones) else ""
    )
    shots["secondaryLane"] = shots["A2 Zone"].apply(
        lambda x: lanes[str(x)[-1]] if str(x)[-1] in lanes else ""
    )
    shots["secondaryPassType"] = shots["A2 Zone"].apply(
        lambda x: pass_types[str(x)[1:-1]] if (str(x)
                                               [1:-1]) in pass_types else ""
    )
    shots["tertiaryZone"] = shots["A3 Zone"].apply(
        lambda x: zones[str(x)[0]] if (
            str(x) != "nan") and (str(x)[0] in zones) else ""
    )
    shots["tertiaryLane"] = shots["A3 Zone"].apply(
        lambda x: lanes[str(x)[-1]] if str(x)[-1] in lanes else ""
    )
    shots["tertiaryPassType"] = shots["A3 Zone"].apply(
        lambda x: pass_types[str(x)[1:-1]] if str(x)[1:-
                                                     1] in pass_types else ""
    )
    shots.rename(
        columns={
            "Team": "team",
            "Shooter": "player",
            "A1": "primaryAssist",
            "A2": "secondaryAssist",
            "A3": "tertiaryAssist",
            "SC?": "chance",
            "Oddman?": "oddman",
        },
        inplace=True,
    )
    shots["type"] = shots["Shot Type"].apply(lambda x: shot_types[x.lower()])
    shots["origin"] = shots["Origin"].apply(
        lambda x: zones[x] if x in zones else x)
    shots["playType"] = shots["Rush?"].apply(
        lambda x: play_types[x] if x in play_types else x
    )
    return shots[
        [
            "period",
            "time",
            "event",
            "type",
            "team",
            "player",
            "primaryAssist",
            "secondaryAssist",
            "tertiaryAssist",
            "chance",
            "playType",
            "oddman",
            "primaryZone",
            "secondaryZone",
            "tertiaryZone",
            "primaryLane",
            "secondaryLane",
            "tertiaryLane",
            "primaryPassType",
            "secondaryPassType",
            "tertiaryPassType",
        ]
    ]


def get_clean_a3z_game_data(file_data, players_dict, teams_dict):
    a3z_pbp = read_a3z_game_data(file_data)
    # Zone Entries

    # 0:3 in all tables as the recombination
    # 3:20 is First group
    shots = a3z_pbp.iloc[:, 0:20]
    # 20:27 is U:AA color starts at 101
    zone_entries = a3z_pbp.iloc[:, np.r_[0:3, 20:27]]
    # 27:32 is AB:AG color starts at 223
    zone_exits = a3z_pbp.iloc[:, np.r_[0:3, 27:32]]
    a3z_final = pd.concat(
        [
            clean_zone_entries(zone_entries),
            clean_zone_exits(zone_exits),
            clean_shots(shots),
        ]
    )
    a3z_final = pd.merge(
        a3z_final,
        a3z_pbp[["period", "time", "seconds"]],
        on=["period", "time"],
        how="left",
    )
    a3z_final["team"] = a3z_final["team"].apply(lambda x: teams_dict[x])
    a3z_final["oppTeam"] = a3z_final["oppTeam"].apply(
        lambda x: teams_dict[x] if x in teams_dict else None  # type: ignore
    )
    a3z_final["player"] = a3z_final[["player", "team"]].apply(
        lambda x: players_dict[(x["team"], x["player"])],
        axis=1,
    )
    a3z_final["oppPlayer"] = a3z_final[["oppPlayer", "oppTeam"]].apply(
        lambda x: players_dict[(x["oppTeam"], x["oppPlayer"])]  # type: ignore
        if (x["oppTeam"], x["oppPlayer"]) in players_dict
        else None,
        axis=1,
    )
    a3z_final["primaryAssist"] = a3z_final[["primaryAssist", "team"]].apply(
        lambda x: players_dict[(x["team"], x["primaryAssist"])]  # type: ignore
        if (x["team"], x["primaryAssist"]) in players_dict
        else None,
        axis=1,
    )
    a3z_final["secondaryAssist"] = a3z_final[["secondaryAssist", "oppTeam"]].apply(
        # type: ignore
        lambda x: players_dict[(x["team"], x["secondaryAssist"])]
        if (x["oppTeam"], x["secondaryAssist"]) in players_dict
        else None,  # type: ignore
        axis=1,
    )
    a3z_final["tertiaryAssist"] = a3z_final[["tertiaryAssist", "team"]].apply(
        # type: ignore
        lambda x: players_dict[(x["team"], x["tertiaryAssist"])]
        if (x["team"], x["tertiaryAssist"]) in players_dict
        else None,  # type: ignore
        axis=1,
    )
    a3z_final["retrieval"] = a3z_final[["retrieval", "team"]].apply(
        lambda x: players_dict[(x["team"], x["retrieval"])]  # type: ignore
        if (x["team"], x["retrieval"]) in players_dict
        else None,
        axis=1,
    )
    a3z_final['period'] = a3z_final['period'].astype(int)
    a3z_final.dropna(how="all", inplace=True, subset=["event"])
    return a3z_final
