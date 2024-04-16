# otree stuff
# Load the Pandas and numpy libraries
import pandas as pd
from otree.api import (
    BaseConstants, BaseSubsession, BaseGroup, BasePlayer
    )

# treat zipcodes

author = 'Benjamin Beranek, Geoffrey Castillo'

doc = """
Import the database
"""


class Constants(BaseConstants):
    name_in_url = 'import'
    players_per_group = None
    num_rounds = 1

    #  _____        _        _
    # |  __ \      | |      | |
    # | |  | | __ _| |_ __ _| |__   __ _ ___  ___
    # | |  | |/ _` | __/ _` | '_ \ / _` / __|/ _ \
    # | |__| | (_| | || (_| | |_) | (_| \__ \  __/
    # |_____/ \__,_|\__\__,_|_.__/ \__,_|___/\___|

    # declare which fields we want to compute the distance
    fields_to_compute_distance = ['sex', 'date', 'miles',
                                  'ethnicity', 'ethnicity_choice', 'race',
                                  'religion', 'religion_denomination',
                                  'country_growing_up', 'us_state_grow_up', 'another_country_grow_up']

    # from this determine which fields we need to import
    fields_to_import = fields_to_compute_distance

    # if there's miles we will need some other fields instead
    if 'miles' in fields_to_compute_distance:
        fields_to_import = [field for field in fields_to_import if field != 'miles']
        extra_fields_for_miles = ['zip', 'city', 'lat', 'long', 'state', 'state_short']
        fields_to_import = fields_to_import + extra_fields_for_miles

    # find out the columns
    fields_to_compute_distance_column = ['player.' + field for field in fields_to_compute_distance]
    fields_to_import_column = ['player.' + field for field in fields_to_import]
    additional_fields_to_import = ['participant.code', 'participant.time_started',
                                   'participant.mturk_worker_id', 'participant.mturk_assignment_id',
                                   'session.code', 'session.mturk_HITId', 'session.mturk_HITGroupId']
    fields_to_import_column = fields_to_import_column + additional_fields_to_import

    # declare which fields need to be normalised
    fields_to_normalise = ['date', 'miles']

    # which columns to parse date
    columns_date = ['participant.time_started', 'player.date']
    columns_to_parse = list(set(columns_date) & set(fields_to_import_column))

    # Read database and change the type of some fields
    # Might be redundant later when we have the real data
    database = pd.read_csv("data.csv",
                           dtype={
                               'player.zip': 'object',
                               'player.ethnicity': 'bool',
                               'player.religion': 'bool',
                               'player.guns': 'bool',
                               'player.us_citizen': 'bool',
                               'player.elementary_secondary_choices_incomplete_high_school': 'Int64'
                               },
                           parse_dates=columns_to_parse,
                           na_values=['NA'],
                           usecols=fields_to_import_column
                           )

    # as the data went through STATA it stripped the time so we apparebtly don't need this anymore
    # if we keep it it transforms datetime to a string
    # # keep only the date, remove the time
    # if 'player.date' in database.columns:
    #     database['player.date'] = database['player.date'].dt.date

    # print("*****************************")
    # print("Database is:")
    # print(database)
    # print("Data types are:")
    # print(database.dtypes)
    # print("*****************************")

    # for the missing values in string variables, need to write NA explicitly,
    # otherwise the python nan is valid only for float variables
    # and the string variables with missing get converted to floats
    for column in database:
        if database[column].dtype == 'object':
            database[column].fillna('NA', inplace=True)

    # get the total number of people in the database
    database_length = len(database.index)

    # declare how many matches we want
    number_matches = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass
