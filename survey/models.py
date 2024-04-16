author = 'Benjamin Beranek, Geoffrey Castillo'

doc = """
Survey and, if needed, distance computation
"""

# date of birth
from bootstrap_datepicker_plus import DatePickerInput
# have a ready-made list of countries according to ISO norm
from django_countries import countries
# have a ready-made list of US states
from localflavor.us.us_states import STATE_CHOICES
from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer
    # Currency as c, currency_range
    )

# import some constants from the import_database
from import_database.models import Constants as database_vars

COUNTRY_CHOICES = list(countries)

# to convert the date-of-birth string into datetime
from datetime import datetime

# treat zipcodes
import zipcodes

# compute the geographic distance
import geopy.distance

# Load the Pandas and numpy libraries
import numpy as np
import pandas as pd

# dump dict as a string
import json

# correctly treat paths, so that they work on Windows, Mac and Linux
from pathlib import Path

from random import randint

main_dir = Path(__file__).resolve().parents[0].with_name('generated_tables')
path_distance_tables = main_dir / 'distance_tables'
path_matched_participants_tables = main_dir / 'matched_participants_tables'


class Constants(BaseConstants):
    name_in_url = 'ds'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


RACE_CHOICES = [
    ('white', 'White'),
    ('black', 'Black or African American'),
    ('american indian', 'American Indian or Alaska Native'),
    ('asian indian', 'Asian Indian'),
    ('chinese', 'Chinese'),
    ('filipino', 'Filipino'),
    ('other asian', 'Other Asian (including Cambodian, Laotian etc.)'),
    ('japanese', 'Japanese'),
    ('korean', 'Korean'),
    ('vietnamese', 'Vietnamese'),
    ('native hawaiian', 'Native Hawaiian'),
    ('guamanian or chamorro', 'Guamanian or Chamorro'),
    ('samoan', 'Samoan'),
    ('other pacific', 'Other Pacific Islander'),
    ('other', 'Other (including Two or more races such as Biracial, Multiracial, etc.)')
    ]


class SurveyPlayer(BasePlayer):
    class Meta:
        abstract = True

    # field to store IP address
    ip = models.StringField()

    # fields to store latitude and longitude of the player (not someone in the database)
    lat = models.FloatField()
    long = models.FloatField()

    # field to store codes of the matches
    matches = models.StringField()

    def save_to_file(self, table, path, filename):
        # save as a file
        path_to_file = path / filename
        if not path_to_file.is_file():
            path.mkdir(parents=True, exist_ok=True)
            table.to_csv(path_to_file, index=False)

    def find_lat_long(self):
        """
        Finds the lat and long for the player
        """
        zipcode = zipcodes.matching(self.zip)
        lat = zipcode[0]['lat']
        long = zipcode[0]['long']
        self.lat = float(lat)
        self.long = float(long)

    def create_distances_table(self):
        """
        Creates the distance table from the database
        :return: the distance table filled with NaN
        """
        fields_to_na = database_vars.fields_to_compute_distance_column

        if 'player.miles' in fields_to_na:
            fields_to_na = [field for field in fields_to_na if field != 'player.miles']
            extra_fields_for_miles = ['zip', 'city', 'lat', 'long']
            fields_to_na = fields_to_na + ['player.' + field for field in extra_fields_for_miles]

        # create a copy of the database for each player
        distances = database_vars.database.copy()

        # indicate the fields with which we want to compute the distance
        # remove the data in the actual fields
        distances[fields_to_na] = np.nan

        return distances

    def compute_distances(self, distances):
        """
        Computes the distances
        :param distances: the distance table
        """
        # import parameters
        database = database_vars.database
        fields_to_normalise = database_vars.fields_to_normalise
        fields_to_compute_distance = database_vars.fields_to_compute_distance
        fields_to_compute_distance_column = database_vars.fields_to_compute_distance_column
        number_fields = len(fields_to_compute_distance)

        # loop over the fields to compute the distance
        for field in fields_to_compute_distance:

            # if field is miles we have to find it using the lat and long
            if field == 'miles':
                # find the difference in miles between player and target
                distances['player.miles'] = [
                    geopy.distance.distance((database_lat, database_long), (self.lat, self.long)).miles
                    for database_lat, database_long in zip(database['player.lat'], database['player.long'])
                    ]


            # if field is date have to convert it to days
            elif field == 'date':
                # get the date from the db
                self_date_string = getattr(self, field)
                # convert it to a date type
                self_date_date = datetime.strptime(self_date_string, '%m/%d/%Y').date()
                # compute the distance
                distances['player.date'] = abs((pd.to_datetime(database['player.date']).dt.date - self_date_date).dt.days)


            # otherwise we check the other fields
            else:
                # get the field value (of the player)
                self_field_value = getattr(self, field)
                # get the field type (of the player)
                self_field_type = self._meta.get_field(field).get_internal_type()
                # get the column name
                column = 'player.' + field

                # if string or bool we just look whether they are equal
                if self_field_type == 'CharField' or self_field_type == 'NullBooleanField' or self_field_type == 'BooleanField':
                    distances[column] = (database[column] != self_field_value)

                # if int or float we look at the difference
                elif self_field_type == 'FloatField' or self_field_type == 'IntegerField':
                    if self_field_value is None:
                        self_field_value = 0
                    distances[column] = abs(database[column] - self_field_value)

                else:
                    print("I haven't done anything with the field:", field)

        # some fields are not between 0 and 1 and so need to be normalised afterwards
        # get the intersection between the fields to use and the fields to normalise
        fields_to_normalise = [field for field in fields_to_normalise if field in fields_to_compute_distance]
        for field in fields_to_normalise:
            column = 'player.' + field
            max = distances[column].max()
            distances[column] = distances[column] / max

        # sum the distances and put them in a new column then normalise
        distances['distance'] = distances[fields_to_compute_distance_column].sum(1) / number_fields

        # sort by the distance column
        distances.sort_values(by=['distance'], inplace=True)
        # reset the index so that participants in the distance table are 0, 1, 2, 3...
        distances.reset_index(drop=True, inplace=True)

        # save as a file
        filename = 'distances_table_' + self.participant.code + '.csv'
        self.save_to_file(distances, path_distance_tables, filename)

    def pass_data_matched_participants(self, distances, matches):
        """
        Extracts from the distance tables the matches that are in position specified by Constants.matches
        :param distances: the distance table
        """
        # import a bunch of parameters
        database = database_vars.database
        fields_to_pass = database_vars.fields_to_import_column

        # get the participant.codes of the participants we want to extract
        match_codes = distances.loc[matches, 'participant.code'].values

        # get the objective social distance
        objective_distances = distances.loc[matches, 'distance'].values

        # extract their data from the database
        match_data = database.loc[database['participant.code'].isin(match_codes), fields_to_pass]

        # we want to have them ordered as in the distances table, because there they are from closest to most distant
        # so we do:
        match_data.set_index('participant.code', inplace=True)
        match_data = match_data.reindex(index=distances.loc[matches, 'participant.code'].values)
        match_data.reset_index(inplace=True)

        # add the objective distances back
        match_data['objective_distance'] = objective_distances

        # place them in the vars
        # the format is [{dict of match1}, {dict of match2}, ...]
        self.participant.vars['matched_participants_data'] = match_data.to_dict('records')

        # remove the starting player.
        for match in range(len(self.participant.vars['matched_participants_data'])):
            for key in fields_to_pass:
                if key.startswith('player.'):
                    new_key = key[7:]
                    self.participant.vars['matched_participants_data'][match][new_key] = self.participant.vars['matched_participants_data'][match].pop(key)

        # serialise as a json and save in database
        self.matches = json.dumps(match_data.to_dict('records'), default=str)

        # save as a file
        filename = 'matched_participants_table_' + self.participant.code + '.csv'
        self.save_to_file(match_data, path_matched_participants_tables, filename)

    def find_matches(self):
        database_length = database_vars.database_length
        matching_method = self.session.config['matching_method']

        # declare how many matches we want
        number_matches = database_vars.number_matches
        # initialise the list containing the matches, of length number_matches
        matches = [0] * number_matches

        if matching_method == 'equally spaced':
            # fill the matches
            # we take the first one, the last one, then we equally space the remaining ones
            matches[0] = 0
            matches[number_matches - 1] = database_length - 1
            # #                       ^ list starts at 0      ^
            for match in range(1, number_matches - 1):
                #     # to have equally-spaced matches
                matches[match] = int(round(match * database_length / (number_matches - 1)))

        elif matching_method == 'random':
            for match in range(0, number_matches):
                matches[match] = randint(0, database_length - 1)

        print(f'matches: {matches}')

        return matches

    def date_error_message(self, value):
        try:
            datetime.strptime(value, '%m/%d/%Y')
        except ValueError:
            return 'Please enter a valid date, the format should be MM/DD/YYYY, for example 10/29/2019'

    def children_number_error_message(self, value):
        if value is not None and value < 1:
            return 'Please enter a number greater than 0.'

    def children_first_age_error_message(self, value):
        if value is not None and value < 1:
            return 'Please enter a number greater than 0.'

    def zip_error_message(self, value):
        if not zipcodes.is_real(value):
            return 'Please enter a valid 5-digit ZIP number.'

    #  _____                                             _     _
    # |  __ \                                           | |   (_)
    # | |  | | ___ _ __ ___   ___   __ _ _ __ __ _ _ __ | |__  _  ___
    # | |  | |/ _ \ '_ ` _ \ / _ \ / _` | '__/ _` | '_ \| '_ \| |/ __|
    # | |__| |  __/ | | | | | (_) | (_| | | | (_| | |_) | | | | | (__
    # |_____/ \___|_| |_| |_|\___/ \__, |_|  \__,_| .__/|_| |_|_|\___|
    #                               __/ |         | |
    #                              |___/          |_|

    sex = models.StringField(
        label='What is your sex?',
        choices=[
            ['male', 'Male'],
            ['female', 'Female']
            ],
        widget=widgets.RadioSelect
        )

    # date = django_models.DateField(
    #     verbose_name='What is your date of birth?',
    #     null=True
    #     )

    date = models.StringField(
        label='What is your date of birth?',
        widget=DatePickerInput(options={
            "format": "MM/DD/YYYY",  # moment date-time format
            "showClose": False,
            "showClear": False,
            "showTodayButton": False,
            "viewMode": 'years',
            "maxDate": '01/01/2010',
            "minDate": '01/01/1909',
            "viewDate": '01/01/1995',
            "defaultDate": False,
            "useCurrent": False
            })
        )

    marital = models.StringField(
        label='What is your marital status?',
        choices=[
            ['married', 'Now married'],
            ['widowed', 'Widowed'],
            ['divorced', 'Divorced'],
            ['separated', 'Separated'],
            ['never', 'Never married']
            ],
        widget=widgets.RadioSelect
        )

    children = models.BooleanField(
        label='Have you had any children?',
        widget=widgets.RadioSelect
        )

    # display if children is True:

    children_number = models.IntegerField(
        label='How many children have you had? Please count all that were born alive at any time (including any you had from a previous relationship).',
        min=1,
        blank=True
        )

    children_first_age = models.IntegerField(
        label='How old were you when your first child was born?',
        min=1,
        blank=True
        )

    language = models.StringField(
        label='What language do you normally speak at home?',
        choices=[
            ['english', 'English'],
            ['spanish', 'Spanish'],
            ['chinese', 'Chinese (including Mandarin and Cantonese)'],
            ['tagalog', 'Tagalog (including Filipino)'],
            ['vietnamese', 'Vietnamese'],
            ['arabic', 'Arabic'],
            ['french', 'French'],
            ['korean', 'Korean'],
            ['russian', 'Russian'],
            ['german', 'German'],
            ['other', 'Other']
            ],
        widget=widgets.RadioSelect
        )

    language_other = models.StringField(
        label='Please enter the language:',
        blank=True
        )

    zip = models.StringField(
        label='What is the ZIP code in which you reside? Please only enter the first 5 numbers.'
        )

    #  _____                    __  _   _           _      _ _
    # |  __ \                  / / | | | |         (_)    (_) |
    # | |__) |__ _  ___ ___   / /__| |_| |__  _ __  _  ___ _| |_ _   _
    # |  _  // _` |/ __/ _ \ / / _ \ __| '_ \| '_ \| |/ __| | __| | | |
    # | | \ \ (_| | (_|  __// /  __/ |_| | | | | | | | (__| | |_| |_| |
    # |_|  \_\__,_|\___\___/_/ \___|\__|_| |_|_| |_|_|\___|_|\__|\__, |
    #                                                             __/ |
    #                                                            |___/

    ethnicity = models.BooleanField(
        label='Are you of Hispanic, Latino, or Spanish origin?',
        widget=widgets.RadioSelect,
        )

    ethnicity_choice = models.StringField(
        label='If yes, which one?',
        choices=[
            ['mexican', 'Mexican, Mexican American, Chicano'],
            ['puerto rican', 'Puerto Rican'],
            ['cuban', 'Cuban'],
            ['other', 'Another Hispanic, Latino, or Spanish origin']
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    ethnicity_choice_other = models.StringField(
        label='Please enter your origin (for example, Argentinean, Colombian, Dominican, Nicaraguan, Salvadoran, Spaniard, and so on):',
        blank=True
        )

    race = models.StringField(
        label='What race do you consider yourself?',
        choices=RACE_CHOICES,
        widget=widgets.RadioSelect
        )

    race_indian_other = models.StringField(
        label='Please enter the name of your enrolled or principal tribe:',
        blank=True
        )

    race_asian_other = models.StringField(
        label='Please enter your race (for example, Hmong, Laotian, Thai, Pakistani, Cambodian, and so on):',
        blank=True
        )

    race_islander_other = models.StringField(
        label='Please enter your race (for example, Fijian, Tongan, and so on):',
        blank=True
        )

    race_other = models.StringField(
        label='Please enter your race:',
        blank=True
        )

    #    _____      _ _       _
    #   |  __ \    | (_)     (_)
    #   | |__) |___| |_  __ _ _  ___  _ __
    #   |  _  // _ \ | |/ _` | |/ _ \| '_ \
    #   | | \ \  __/ | | (_| | | (_) | | | |
    #   |_|  \_\___|_|_|\__, |_|\___/|_| |_|
    #                    __/ |
    #                   |___/

    religion = models.BooleanField(
        label='Do you belong to a religious denomination?',
        widget=widgets.RadioSelect
        )

    religion_denomination = models.StringField(
        label='Which religious denomination do you belong to?',
        choices=[
            ['roman catholic', 'Roman Catholic'],
            ['protestant', 'Protestant'],
            ['mormon', 'Mormon'],
            ['orthodox', 'Orthodox (Russian/Greek/etc.)'],
            ['jewish', 'Jew'],
            ['muslim', 'Muslim'],
            ['hindu', 'Hindu'],
            ['buddhist', 'Buddhist'],
            ['other', 'Other denomination']
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    religion_denomination_other = models.StringField(
        label='Please enter your religious denomination:',
        blank=True
        )

    #    _    _
    #   | |  | |
    #   | |__| | ___  _ __ ___   ___
    #   |  __  |/ _ \| '_ ` _ \ / _ \
    #   | |  | | (_) | | | | | |  __/
    #   |_|  |_|\___/|_| |_| |_|\___|
    #
    #

    home = models.StringField(
        label='Which best describes the building where you live?',
        choices=[
            ['mobile home', 'A mobile home'],
            ['one family detached', 'A one-family house detached from any other house'],
            ['one family attached', 'A one-family house attached to one or more houses'],
            ['less than five apartment', 'A building with less than 5 apartments'],
            ['five or more apartments', 'A building with 5 or more apartments'],
            ['dorm', 'A dormitory or hall of residence'],
            ['boat', 'Boat, RV, van etc.'],
            ['other', 'Other']
            ],
        widget=widgets.RadioSelect
        )

    home_other = models.StringField(
        label='Please enter the type of building you live in:',
        blank=True
        )

    guns = models.BooleanField(
        label='Do you happen to have in your home any guns or revolvers?',
        widget=widgets.RadioSelect
        )

    place_growing_up = models.StringField(
        label='Which of the categories comes closest to the type of place you were living in when you were 16 years old?',
        choices=[
            ['open country', 'In open country but not on a farm'],
            ['farm', 'On a farm'],
            ['small town', 'In a small city or town (under 50,000)'],
            ['medium city', 'In a medium-size city (50,000-250,000)'],
            ['suburb', 'In a suburb near a large city'],
            ['large city', 'In a large city (over 250,000)'],
            ],
        widget=widgets.RadioSelect
        )

    # LOOK GEOFFREY: Can we embolden the word "closest" in the place_growing_up questions above?

    #     _____                   _                                             _   ______    _                 _   _
    #    / ____|                 (_)                                           | | |  ____|  | |               | | (_)
    #   | |  __ _ __ _____      ___ _ __   __ _   _   _ _ __     __ _ _ __   __| | | |__   __| |_   _  ___ __ _| |_ _  ___  _ __
    #   | | |_ | '__/ _ \ \ /\ / / | '_ \ / _` | | | | | '_ \   / _` | '_ \ / _` | |  __| / _` | | | |/ __/ _` | __| |/ _ \| '_ \
    #   | |__| | | | (_) \ V  V /| | | | | (_| | | |_| | |_) | | (_| | | | | (_| | | |___| (_| | |_| | (_| (_| | |_| | (_) | | | |
    #    \_____|_|  \___/ \_/\_/ |_|_| |_|\__, |  \__,_| .__/   \__,_|_| |_|\__,_| |______\__,_|\__,_|\___\__,_|\__|_|\___/|_| |_|
    #                                      __/ |       | |
    #                                     |___/        |_|

    highest_degree = models.StringField(
        # note: in order to have the word 'highest' bold I input it by hand in the html, so changing the label here won't change the label on the html
        label='What is the highest degree or level of school you have COMPLETED? If currently enrolled, mark the previous grade or highest degree received.',
        choices=[
            ['no schooling', 'No schooling completed'],
            ['elementary or some secondary schooling', 'Nursery or preschool through grade 12'],
            ['12th grade no degree', '12th grade – no diploma'],
            ['high school graduate', 'High school graduate'],
            ['college or some college', 'College or some college'],
            ['beyond bachelors', "Postgraduate education"],
            ],
        widget=widgets.RadioSelect
        )

    elementary_secondary_choices = models.StringField(
        choices=[
            ['nursery school', 'Nursery school'],
            ['kindergarten', 'Kindergarten'],
            ['incomplete high school', 'Grade 1 through 11']
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    elementary_secondary_choices_incomplete_high_school = models.IntegerField(
        label='Specify the highest grade completed:',
        blank=True,
        min=1,
        max=11
        )

    high_school_choices = models.StringField(
        choices=[
            ['high school diploma', 'Regular high school diploma'],
            ['GED', 'GED or alternative credential'],
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    college_choices = models.StringField(
        choices=[
            ['less than 1 year college', 'Some college credit, but less than 1 year of college credit'],
            ['more than 1 year college, no degree', '1 or more years of college credit, no degree'],
            ['associates degree', 'Associate’s degree (for example: AA, AS)'],
            ['bachelors degree', 'Bachelor’s degree (for example: BA, BS)'],
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    after_bachelor_choices = models.StringField(
        choices=[
            ['masters degree', 'Master’s degree (for example: MA, MS, MEng,MEd, MSW, MBA)'],
            ['professional degree',
             'Professional degree beyond a bachelor’s degree(for example: MD, DDS, DVM, LLB, JD)'],
            ['doctorate', 'Doctorate Degree (for example: PhD, EdD)']
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    # LOOK GEOFFREY: Can we embolden the word "highest" in the highest_degree questions above?
    # A: done

    # LOOK GEOFFREY: We originally wanted to have just the ALL CAPS options appear and thereafter have the subsequent choices appear. Can we do that?
    # A: done

    # intended_major = models.StringField(
    #     label='What is your current major or what do you intend to major in? (For example: chemical engineering, elementary teacher education, organizational psychology)'
    # )

    # LOOK GEOFFREY: This question is meant to appear if 'less than 1 year college' or 'more than 1 year college, no degree' is selected in highest_degree question above.
    # A: finally I've split them before bachelor/after bachelor... otherwise it was a coding nightmare. This way if people have a bachelor we can for use ask for the actual major

    major_college = models.StringField(
        label='What has been your main area of study? (For example a major like chemical engineering, elementary education, nursing, or organizational psychology)',
        blank=True
        )

    major_bachelor = models.StringField(
        label='What has been your main area of study? (For example a major like chemical engineering, elementary education, nursing, or organizational psychology)',
        blank=True
        )

    # LOOK GEOFFREY: This question is meant to appear if 'associates degree' or higher is selected in highest_degree question above.

    #     ____       _       _
    #    / __ \     (_)     (_)
    #   | |  | |_ __ _  __ _ _ _ __
    #   | |  | | '__| |/ _` | | '_ \
    #   | |__| | |  | | (_| | | | | |
    #    \____/|_|  |_|\__, |_|_| |_|
    #                   __/ |
    #                  |___/

    country_growing_up = models.StringField(
        label='Where did you grow up?',
        choices=[
            ['usa', 'In the the United States'],
            ['another country', 'In another country'],
            ],
        widget=widgets.RadioSelect
        )

    us_state_grow_up = models.StringField(
        label='Please select the State or Territory in which you grew up',
        choices=STATE_CHOICES,
        blank=True
        )

    another_country_grow_up = models.StringField(
        label='Please select the country in which you grew up:',
        choices=COUNTRY_CHOICES,
        blank=True
        )

    us_citizen = models.BooleanField(
        label='Are you a citizen of the United States?',
        widget=widgets.RadioSelect
        )

    us_citizen_options = models.StringField(
        label='Were you:',
        choices=[
            ['born usa', 'Born in the United States'],
            ['born us territory', 'Born in American Samoa, Guam, the Northern Mariana Islands, Puerto Rico, or the Virgin Islands'],
            ['born abroad us parents', 'Born abroad of United States citizen parent or parents'],
            ['naturalized us citizen', 'United States citizen by naturalization'],
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    #   __          __        _
    #   \ \        / /       | |
    #    \ \  /\  / /__  _ __| | __
    #     \ \/  \/ / _ \| '__| |/ /
    #      \  /\  / (_) | |  |   <
    #       \/  \/ \___/|_|  |_|\_\
    #
    #

    work_last_week = models.StringField(
        label='What were you doing for the majority of last week?',
        choices=[
            ['full time work', 'Working full time'],
            ['part time work', 'Working part time'],
            ['school', 'Studying'],
            ['housework', 'Keeping house'],
            ],
        widget=widgets.RadioSelect
        )

    profession = models.StringField(
        label='What do you do for work? Please write your profession:',
        blank=True
        )

    employer = models.StringField(
        label='What category best describes your employer?',
        choices=[
            ['government employer', 'Government or public institution'],
            ['private business', 'Private business or industry'],
            ['private non profit', 'Private non-profit organization'],
            ['self employed', 'I am self employed'],
            ],
        widget=widgets.RadioSelect,
        blank=True
        )

    work_tasks = models.FloatField(
        label='Are the tasks you do at work mostly manual or mostly intellectual? Please select the number where 1 means “mostly manual tasks” and 10 means “mostly intellectual tasks”',
        choices=[
            [0, '1'],
            [1 / 9, '2'],
            [2 / 9, '3'],
            [3 / 9, '4'],
            [4 / 9, '5'],
            [5 / 9, '6'],
            [6 / 9, '7'],
            [7 / 9, '8'],
            [8 / 9, '9'],
            [1, '10'],
            ],
        widget=widgets.RadioSelectHorizontal,
        blank=True
        )

    unemployed_10_years = models.BooleanField(
        label='At any time during the last ten years, have you been unemployed and looking for work for as long as a month?',
        widget=widgets.RadioSelect
        )

    labor_union = models.BooleanField(
        label='Do you belong to a labor union?',
        widget=widgets.RadioSelect
        )

    #    ______                                _         _____                                 _
    #   |  ____|                              (_)       / ____|                               (_)
    #   | |__   ___ ___  _ __   ___  _ __ ___  _  ___  | |     ___  _ __ ___  _ __   __ _ _ __ _ ___  ___  _ __  ___
    #   |  __| / __/ _ \| '_ \ / _ \| '_ ` _ \| |/ __| | |    / _ \| '_ ` _ \| '_ \ / _` | '__| / __|/ _ \| '_ \/ __|
    #   | |___| (_| (_) | | | | (_) | | | | | | | (__  | |___| (_) | | | | | | |_) | (_| | |  | \__ \ (_) | | | \__ \
    #   |______\___\___/|_| |_|\___/|_| |_| |_|_|\___|  \_____\___/|_| |_| |_| .__/ \__,_|_|  |_|___/\___/|_| |_|___/
    #                                                                        | |
    #                                                                        |_|

    household_income = models.FloatField(
        label='To the best of your knowledge, in which of these groups did your total household income from all sources (before taxes) fall last year? (If you are a student who is supported financially by your family, please include their income in your calculation of household income.)',
        choices=[
            [0, 'Under $1,000'],
            [1 / 24, '$1,000 to $2,999'],
            [2 / 24, '$3,000 to $3,999'],
            [3 / 24, '$4,000 to $4,999'],
            [4 / 24, '$5,000 to $5,999'],
            [5 / 24, '$6,000 to $6,999'],
            [6 / 24, '$7,000 to $7,999'],
            [7 / 24, '$8,000 to $9,999'],
            [8 / 24, '$10,000 to $12,499'],
            [9 / 24, '$12,500 to $14,999'],
            [10 / 24, '$15,000 to $17,499'],
            [11 / 24, '$17,500 to $19,999'],
            [12 / 24, '$20,000 to $22,499'],
            [13 / 24, '$22,500 to $24,999'],
            [14 / 24, '$25,000 to $29,999'],
            [15 / 24, '$30,000 to $34,999'],
            [16 / 24, '$35,000 to $39,999'],
            [17 / 24, '$40,000 to $49,999'],
            [18 / 24, '$50,000 to $59,999'],
            [19 / 24, '$60,000 to $74,999'],
            [20 / 24, '$75,000 to $89,999'],
            [21 / 24, '$90,000 to $109,999'],
            [22 / 24, '$110,000 to $129,999'],
            [23 / 24, '$130,000 to $149,999'],
            [1, '$150,000 or over'],
            ],
        widget=widgets.RadioSelect
        )

    income_group_placement = models.FloatField(
        label='Imagine an income scale from 1 to 10 where 1 indicates the lowest income group in America and 10 indicates the highest income group. Counting all wages, salaries, pensions and other incomes that come in, please specify what income group your household is in:',
        choices=[
            [0, '1'],
            [1 / 9, '2'],
            [2 / 9, '3'],
            [3 / 9, '4'],
            [4 / 9, '5'],
            [5 / 9, '6'],
            [6 / 9, '7'],
            [7 / 9, '8'],
            [8 / 9, '9'],
            [1, '10'],
            ],
        widget=widgets.RadioSelectHorizontal
        )

    sixteen_yo_comparison = models.FloatField(
        label='Thinking about the time when you were 16 years old, compared with families in general then, where would you say your family income was?',
        choices=[
            [0, 'Far below average'],
            [1 / 4, 'Below average'],
            [2 / 4, 'Average'],
            [3 / 4, 'Above average'],
            [1, 'Far above average'],
            ],
        widget=widgets.RadioSelect
        )

    parental_comparison_standards = models.FloatField(
        label='Compared to your parents when they were the age you are now, do you think your own standard of living now is:',
        choices=[
            [1, 'Much better'],
            [3 / 4, 'Somewhat better'],
            [2 / 4, 'About the same'],
            [1 / 4, 'Somewhat worse'],
            [0, 'Much worse'],
            ],
        widget=widgets.RadioSelect
        )

    social_class = models.StringField(
        label='If you were asked to use one of four names for your social class, which would you say you belong in?',
        choices=[
            ['lower class', 'the Lower Class'],
            ['working class', 'the Working Class'],
            ['middle class', 'the Middle Class'],
            ['upper class', 'the Upper Class'],
            ],
        widget=widgets.RadioSelect
        )

    financial_satisfaction = models.FloatField(
        label='How satisfied are you with the present financial situation of you and your family?',
        choices=[
            [1, 'Pretty well satisfied with my present financial situation'],
            [1 / 2, 'More or less satisfied with my present financial situation'],
            [0, 'Not satisfied at all with my present financial situation'],
            ],
        widget=widgets.RadioSelect
        )

    #    _   _       _   _                   _ _                   _______
    #   | \ | |     | | (_)                 | (_)                 / / ____|
    #   |  \| | __ _| |_ _  ___  _ __   __ _| |_ ___ _ __ ___    / / |  __  _____   _____ _ __ _ __   __ _ _ __   ___ ___
    #   | . ` |/ _` | __| |/ _ \| '_ \ / _` | | / __| '_ ` _ \  / /| | |_ |/ _ \ \ / / _ \ '__| '_ \ / _` | '_ \ / __/ _ \
    #   | |\  | (_| | |_| | (_) | | | | (_| | | \__ \ | | | | |/ / | |__| | (_) \ V /  __/ |  | | | | (_| | | | | (_|  __/
    #   |_| \_|\__,_|\__|_|\___/|_| |_|\__,_|_|_|___/_| |_| |_/_/   \_____|\___/ \_/ \___|_|  |_| |_|\__,_|_| |_|\___\___|
    #
    #

    importance_democracy = models.FloatField(
        label='How important is it for you to live in a country that is governed democratically? Please indicate the importance on a scale where 1 means it is “not at all important” and 10 means “absolutely important”.',
        choices=[
            [0, '1'],
            [1 / 9, '2'],
            [2 / 9, '3'],
            [3 / 9, '4'],
            [4 / 9, '5'],
            [5 / 9, '6'],
            [6 / 9, '7'],
            [7 / 9, '8'],
            [8 / 9, '9'],
            [1, '10'],
            ],
        widget=widgets.RadioSelectHorizontal
        )

    american_pride = models.FloatField(
        label='How proud are you to live in the United States?',
        choices=[
            [1, 'Very proud'],
            [2 / 3, 'Quite proud'],
            [1 / 3, 'Not very proud'],
            [0, 'Not at all proud'],
            ],
        widget=widgets.RadioSelect
        )

    #    _____      _ _ _   _           _  __      ___
    #   |  __ \    | (_) | (_)         | | \ \    / (_)
    #   | |__) |__ | |_| |_ _  ___ __ _| |  \ \  / / _  _____      _____
    #   |  ___/ _ \| | | __| |/ __/ _` | |   \ \/ / | |/ _ \ \ /\ / / __|
    #   | |  | (_) | | | |_| | (_| (_| | |    \  /  | |  __/\ V  V /\__ \
    #   |_|   \___/|_|_|\__|_|\___\__,_|_|     \/   |_|\___| \_/\_/ |___/
    #
    #

    political_party = models.StringField(
        label='Generally speaking, do you usually think of yourself as a Democrat, a Republican, an Independent, or what?',
        choices=[
            ['democrat', 'Democrat'],
            ['republican', 'Republican'],
            ['independent', 'Independent'],
            ['other party', 'Other party'],
            ['no preference', 'No preference'],
            ],
        widget=widgets.RadioSelect
        )

    other_political_party = models.StringField(
        label='What other political party do you identify with:',
        blank=True
        )

    politcal_views = models.FloatField(
        label='We hear a lot of talk these days about liberals and conservatives. Here is a seven-point scale on which the political views that people might hold are arranged from extremely liberal to extremely conservative. Where would you place YOURSELF on this scale?',
        choices=[
            [0, 'Extremely liberal'],
            [1 / 6, 'Liberal'],
            [2 / 6, 'Slightly liberal'],
            [3 / 6, 'Moderate; middle of the road'],
            [4 / 6, 'Slightly conservative'],
            [5 / 6, 'Conservative'],
            [1, 'Extremely conservative'],
            ],
        widget=widgets.RadioSelect
        )

    #     _____             __ _     _                       _         _____           _   _ _         _   _
    #    / ____|           / _(_)   | |                     (_)       |_   _|         | | (_) |       | | (_)
    #   | |     ___  _ __ | |_ _  __| | ___ _ __   ___ ___   _ _ __     | |  _ __  ___| |_ _| |_ _   _| |_ _  ___  _ __  ___
    #   | |    / _ \| '_ \|  _| |/ _` |/ _ \ '_ \ / __/ _ \ | | '_ \    | | | '_ \/ __| __| | __| | | | __| |/ _ \| '_ \/ __|
    #   | |___| (_) | | | | | | | (_| |  __/ | | | (_|  __/ | | | | |  _| |_| | | \__ \ |_| | |_| |_| | |_| | (_) | | | \__ \
    #    \_____\___/|_| |_|_| |_|\__,_|\___|_| |_|\___\___| |_|_| |_| |_____|_| |_|___/\__|_|\__|\__,_|\__|_|\___/|_| |_|___/
    #
    #

    # we will input the main label ('The table below lists some institutions in this country. As far as the people running these institutions...
    # ...are concerned, would you say you currently have a great deal of confidence, only some confidence, or hardly any confidence at all in them?') directly in the HTML
    # for the moment we can also leave out the 'A great deal of confidence' etc. since it's common to several options

    executive_branch_confidence = models.FloatField(
        label='Executive Branch of the Federal Government',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    congress_confidence = models.FloatField(
        label='Congress',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    supreme_court_confidence = models.FloatField(
        label='the Supreme Court',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    military_confidence = models.FloatField(
        label='the Military',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    police_confidence = models.FloatField(
        label='the Police',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    banks_confidence = models.FloatField(
        label='Banks and Financial Institutions',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    unions_confidence = models.FloatField(
        label='Organized Labor (or Unions)',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    public_ed_confidence = models.FloatField(
        label='Public Education',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    press_confidence = models.FloatField(
        label='the Press',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    #     _____                  _      _____                      _ _               _____      _            _ _   _
    #    / ____|                | |    / ____|                    | (_)             |  __ \    (_)          (_) | (_)
    #   | |  __  _____   ___ __ | |_  | (___  _ __   ___ _ __   __| |_ _ __   __ _  | |__) | __ _  ___  _ __ _| |_ _  ___  ___
    #   | | |_ |/ _ \ \ / / '_ \| __|  \___ \| '_ \ / _ \ '_ \ / _` | | '_ \ / _` | |  ___/ '__| |/ _ \| '__| | __| |/ _ \/ __|
    #   | |__| | (_) \ V /| | | | |_   ____) | |_) |  __/ | | | (_| | | | | | (_| | | |   | |  | | (_) | |  | | |_| |  __/\__ \
    #    \_____|\___/ \_/ |_| |_|\__| |_____/| .__/ \___|_| |_|\__,_|_|_| |_|\__, | |_|   |_|  |_|\___/|_|  |_|\__|_|\___||___/
    #                                        | |                              __/ |
    #                                        |_|                             |___/

    # example for GSS95
    # we will input the main label ('We are faced with many problems in this country...') directly in the HTML
    # for the moment we can also leave out the 'Spending too much' etc. since it's common to several options

    improve_condition_blacks = models.FloatField(
        label='Improving the conditions of African Americans',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    improve_condition_abroad = models.FloatField(
        label='Improving the conditions of those living in Foreign Countries',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    protecting_environment = models.FloatField(
        label='Improving and protecting the Environment',
        choices=[0, 1 / 2, 1],
        widget=widgets.RadioSelect
        )

    government_redistribution = models.FloatField(
        label='''On a seven-point scale, where 1 means very important and 7 means not important at all, 
        how important do you think it is for the government in Washington to reduce the differences in income between the rich and the poor?''',
        choices=[
            [0, '1'],
            [1 / 6, '2'],
            [2 / 6, '3'],
            [3 / 6, '4'],
            [4 / 6, '5'],
            [5 / 6, '6'],
            [1, '7']
            ],
        widget=widgets.RadioSelectHorizontal
        )

    income_tax_level = models.FloatField(
        label='Do you consider the amount of federal income tax we pay as too high, about right, or too low?',
        choices=[
            [1, 'The federal income tax I pay is too high'],
            [1 / 2, 'The federal income tax I pay is about right'],
            [0, 'The federal income tax I pay is too low'],
            ],
        widget=widgets.RadioSelect
        )

    death_penalty = models.BooleanField(
        label='Do you favor or oppose the death penalty for persons convicted of murder?',
        choices=[
            [True, 'I favor the death penalty for persons convicted of murder'],
            [False, 'I oppose the death penalty for persons convicted of murder'],
            ],
        widget=widgets.RadioSelect
        )

    #    _____                  _____      _       _   _                                      __  __ _                      _   _                          _   _
    #   |  __ \                |  __ \    | |     | | (_)                   ___        /\    / _|/ _(_)                    | | (_)               /\       | | (_)
    #   | |__) |__ _  ___ ___  | |__) |___| | __ _| |_ _  ___  _ __  ___   ( _ )      /  \  | |_| |_ _ _ __ _ __ ___   __ _| |_ ___   _____     /  \   ___| |_ _  ___  _ __
    #   |  _  // _` |/ __/ _ \ |  _  // _ \ |/ _` | __| |/ _ \| '_ \/ __|  / _ \/\   / /\ \ |  _|  _| | '__| '_ ` _ \ / _` | __| \ \ / / _ \   / /\ \ / __| __| |/ _ \| '_ \
    #   | | \ \ (_| | (_|  __/ | | \ \  __/ | (_| | |_| | (_) | | | \__ \ | (_>  <  / ____ \| | | | | | |  | | | | | | (_| | |_| |\ V /  __/  / ____ \ (__| |_| | (_) | | | |
    #   |_|  \_\__,_|\___\___| |_|  \_\___|_|\__,_|\__|_|\___/|_| |_|___/  \___/\/ /_/    \_\_| |_| |_|_|  |_| |_| |_|\__,_|\__|_| \_/ \___| /_/    \_\___|\__|_|\___/|_| |_|
    #
    #

    affirmative_action = models.FloatField(
        label='''Are you for preferential hiring and promotion of African Americans or are you against it? 
        Common considerations when evaluating this policy include the past discrimination of African Americans as well as 
        the discriminatory impact of this policy on others.''',
        choices=[
            [0, 'Strongly opposed to giving preference to African Americans in hiring and promotion'],
            [1 / 3, 'Somewhat opposed to giving preference to African Americans in hiring and promotion'],
            [2 / 3, 'Somewhat in favor of giving preference to African Americans in hiring and promotion'],
            [1, 'Strongly in favor of giving preference to African Americans in hiring and promotion']
            ],
        widget=widgets.RadioSelect
        )

    #    _____
    #   / ____|
    #  | (___   _____  __
    #   \___ \ / _ \ \/ /
    #   ____) |  __/>  <
    #  |_____/ \___/_/\_\

    sex_before_marriage = models.FloatField(
        label='In your opinion, if two consensual adults have sexual relations before marriage, do you think it is:',
        choices=[
            [0, 'Always wrong'],
            [1 / 3, 'Almost always wrong'],
            [2 / 3, 'Wrong only sometimes'],
            [1, 'Not wrong at all'],
            ],
        widget=widgets.RadioSelect
        )

    same_sex_relations = models.FloatField(
        label='Similarly, if two consensual adults of the same sex have sexual relations, do you think it is:',
        choices=[
            [0, 'Always wrong'],
            [1 / 3, 'Almost always wrong'],
            [2 / 3, 'Wrong only sometimes'],
            [1, 'Not wrong at all'],
            ],
        widget=widgets.RadioSelect
        )

    abortion = models.BooleanField(
        label='Do you think it should be possible for a pregnant woman to obtain a legal abortion if the woman wants one for any reason?',
        choices=[
            [True, 'Yes, it should be possible'],
            [False, 'No, it should not be possible'],
            ],
        widget=widgets.RadioSelect
        )

    #     _____                           _   _____                        _   _                      __    ____  _   _
    #    / ____|                         | | |  __ \                      | | (_)                    / _|  / __ \| | | |
    #   | |  __  ___ _ __   ___ _ __ __ _| | | |__) |__ _ __ ___ ___ _ __ | |_ _  ___  _ __     ___ | |_  | |  | | |_| |__   ___ _ __ ___
    #   | | |_ |/ _ \ '_ \ / _ \ '__/ _` | | |  ___/ _ \ '__/ __/ _ \ '_ \| __| |/ _ \| '_ \   / _ \|  _| | |  | | __| '_ \ / _ \ '__/ __|
    #   | |__| |  __/ | | |  __/ | | (_| | | | |  |  __/ | | (_|  __/ |_) | |_| | (_) | | | | | (_) | |   | |__| | |_| | | |  __/ |  \__ \
    #    \_____|\___|_| |_|\___|_|  \__,_|_| |_|   \___|_|  \___\___| .__/ \__|_|\___/|_| |_|  \___/|_|    \____/ \__|_| |_|\___|_|  |___/
    #                                                               | |
    #                                                               |_|

    people_helpful = models.BooleanField(
        label='Would you say that most of the time people try to be helpful, or that they are mostly just looking out for themselves?',
        choices=[
            [True, 'Most of the time people try to be helpful'],
            [False, 'People are mostly just looking out for themselves'],
            ],
        widget=widgets.RadioSelect
        )

    people_take_advantage_of_you = models.BooleanField(
        label='Do you think most people would try to take advantage of you if they got a chance, or would they try to be fair?',
        choices=[
            [True, 'Most people would try to take advantage of you if they got a chance'],
            [False, 'Most people would try to be fair'],
            ],
        widget=widgets.RadioSelect
        )

    people_trustworthy = models.BooleanField(
        label='Generally speaking, would you say that most people can be trusted or that you can not be too careful in dealing with people?',
        choices=[
            [True, 'Most people can be trusted'],
            [False, 'You cannot be too careful in dealing with people'],
            ],
        widget=widgets.RadioSelect
        )


class Player(SurveyPlayer):
    pass
