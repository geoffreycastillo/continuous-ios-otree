author = 'Benjamin Beranek, Geoffrey Castillo'

doc = """
Take the matches, generate the long, narrative display, then display them.
"""

from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
    )

# import the Player class of the survey so that we can look through the field choices
from survey.models import RACE_CHOICES

# have a ready-made list of US states
from localflavor.us.us_states import STATE_CHOICES

# have a ready-made list of countries according to ISO norm
from django_countries import countries

COUNTRY_CHOICES = list(countries)

# to shuffle the lists
import random

# import the constants of the distance measure so that we can get the number of matches
from import_database.models import Constants as database_vars

# to display the age
from datetime import date


class Constants(BaseConstants):
    name_in_url = 'dmn'
    players_per_group = None

    num_matches = database_vars.number_matches
    num_rounds = num_matches

    matches_range = list(range(num_rounds))
    if num_rounds <= 4:
        matches_names = ['Heart', 'Diamond', 'Spade', 'Club']

    length_tweet = 25 if num_matches > 1 else 50


class Subsession(BaseSubsession):

    def creating_session(self):
        for player in self.get_players():
            if self.round_number == 1:
                player.participant.vars['narrative_sequence'] = player.determine_order()
                player.participant.vars['matches_names'] = player.determine_matches_names()

    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    def determine_matches_names(self):
        """
        Randomises the names of the matches
        :return: a list of the names
        For example with 4 matches: [0, 1, 2, 3]
        And a return of ['Club', 'Heart', 'Spade', 'Diamond']
        It means that for the duration of the experiment, match 0 will be 'Club', match 1 will be 'Heart' and so on
        """

        # number of matches we need
        required_length = Constants.num_rounds
        matches_names = Constants.matches_names.copy()
        random.shuffle(matches_names)

        # cut the end of the list of names if needed
        matches_names = matches_names[:required_length]

        return matches_names

    def determine_order(self):
        """
        Randomises order of the matches
        :return list narrative_sequence: the order of the matches
        """
        narrative_sequence = Constants.matches_range.copy()
        random.shuffle(narrative_sequence)

        return narrative_sequence

    def generate_card_text(self, input):
        """
        Generate the card text for a single match
        :param input: the data of the match
        :return: formatted text in human-readable form
        """
        output = {}

        if input['sex'] == 'male':
            output['pronoun'] = 'he'
            output['Pronoun'] = output['pronoun'].capitalize()
            output['possessive'] = 'his'
            output['reflexive'] = 'himself'
        else:
            output['pronoun'] = 'she'
            output['Pronoun'] = output['pronoun'].capitalize()
            output['possessive'] = 'her'
            output['reflexive'] = 'herself'

        output['sex'] = 'man' if input['sex'] == 'male' else 'woman'

        # city, state
        output['city'] = input['city']
        output['state'] = input['state']
        output['state_short'] = input['state_short']

        # age
        output['age'] = date.today().year - input['date'].year

        # race, ethnicity
        if input['ethnicity_choice'] == 'mexican':
            output['ethnicity_choice'] = 'Mexican, Mexican American, or Chicano'
        elif input['ethnicity_choice'] == 'puerto rican':
            output['ethnicity_choice'] = 'Puerto Rican'
        elif input['ethnicity_choice'] == 'cuban':
            output['ethnicity_choice'] = 'Cuban'
        else:
            output['ethnicity_choice'] = 'Hispanic, Latino, or Spanish origin but not Mexican, Puerto Rican, or Cuban'

        for key, value in RACE_CHOICES:
            if key == input['race']:
                if input['race'] == 'white':
                    output['race-ethnicity'] = 'white'
                elif input['race'] == 'other pacific':
                    output['race-ethnicity'] = 'a Pacific Islander, but not Native Hawaiian, Guamanian or Chamorro, or Samoan'
                elif input['race'] == 'other asian':
                    output['race-ethnicity'] = 'Asian, but not Asian Indian, Chinese, or Filipino,'
                else:
                    output['race-ethnicity'] = value

        if input['ethnicity'] == 1:
            output['race-ethnicity'] = output['race-ethnicity'] + ' and considers ' + output['reflexive'] + ' to be of ' + output['ethnicity_choice'] + ' origin'

        # religion
        if input['religion'] == 0:
            output['religion-denomination'] = 'does not belong to a religious denomination'
        else:
            output['religion-denomination'] = 'adheres to ' + input['religion_denomination'].title() + ' beliefs'

        # growing up
        for key, value in STATE_CHOICES:
            if key == input['us_state_grow_up']:
                output['us_state_grow_up'] = value

        for key, value in COUNTRY_CHOICES:
            if key == input['another_country_grow_up']:
                output['another_country_grow_up'] = value

        if output['another_country_grow_up'] in ['Bahamas', 'Cayman Islands', 'Central African Republic', 'Channel Islands', 'Comoros', 'Czech Republic',
                                                 'Dominican Republic', 'Falkland Islands', 'Gambia', 'Isle of Man', 'Ivory Coast', 'Leeward Islands',
                                                 'Maldives', 'Marshall Islands', 'Netherlands', 'Philippines', 'Solomon Islands', 'Turks and Caicos Islands',
                                                 'United Arab Emirates', 'United Kingdom', 'Virgin Islands']:
            output['another_country_grow_up'] = 'the ' + output['another_country_grow_up']

        if input['country_growing_up'] == 'usa':
            output['country_growing_up'] = output['us_state_grow_up'] + ' in the United States'
        else:
            output['country_growing_up'] = output['another_country_grow_up']

        # not used:
        # {m[Pronoun]} {m[marital]}."
        # {m[Pronoun]} is {m[us_citizen]}.
        # {m[Pronoun]} completed {m[highest_degree]}.
        # For the majority of last week {m[pronoun]} was {m[work_last_week]}
        # {m[Pronoun]} sees {m[reflexive]} as belonging to {m[social_class]}.
        # {m[Pronoun]} thinks of {m[reflexive]} as {m[political_party]} and describes {m[possessive]} political views as {m[politcal_views]}.

        # constuct the text
        return """This participant is a {m[sex]} from {m[city]}, {m[state]}, who is {m[age]} years old. 
                            {m[Pronoun]} is {m[race-ethnicity]}.
                            {m[Pronoun]} {m[religion-denomination]}.
                            {m[Pronoun]} grew up in {m[country_growing_up]}.
                            """.format(m=output)

    def generate_display(self, number_matches=database_vars.number_matches):
        """
        Generates the narrative display, which will be passed to the pages.
        :return: The formatted narrative of all matches in a list, where each item in the list is a different match
        """

        # initialise
        display = [''] * number_matches

        # constuct the text
        for match in range(number_matches):
            display[match] = self.generate_card_text(self.participant.vars['matched_participants_data'][match])

        return display

        # not used now, might be used later

        # display_data['marital'] = 'has never been married' if data_match['marital'] == 'never' else 'is ' + data_match[
        #     'marital']

        # if data_match['elementary_secondary_choices'] == 'incomplete':
        #     if data_match['elementary_secondary_choices_incomplete_high_school'] == 1:
        #         display_data[
        #             'elementary_secondary_choices'] = display_data['elementary_secondary_choices_incomplete_high_school'] + 'st grade'
        # elif data_match['elementary_secondary_choices'] == 'incomplete':
        #     if data_match['elementary_secondary_choices_incomplete_high_school'] == 2:
        #         display_data['elementary_secondary_choices'] = display_data['elementary_secondary_choices_incomplete_high_school'] + 'nd grade'
        # elif data_match['elementary_secondary_choices'] == 'incomplete':
        #     if data_match['elementary_secondary_choices_incomplete_high_school'] == 3:
        #         display_data['elementary_secondary_choices'] = display_data['elementary_secondary_choices_incomplete_high_school'] + 'rd grade'
        # elif data_match['elementary_secondary_choices'] == 'incomplete':
        #     if data_match['elementary_secondary_choices_incomplete_high_school'] > 3:
        #         display_data['elementary_secondary_choices'] = display_data['elementary_secondary_choices_incomplete_high_school'] + 'th grade'
        # elif data_match['elementary_secondary_choices'] == 'kindergarten':
        #     display_data['elementary_secondary_choices'] = 'kindergarten'
        # else:
        #     display_data['elementary_secondary_choices'] = 'nursery school'

        # if data_match['high_school_choices'] == 'high school diploma':
        #     display_data['high_school_choices'] = '12th grade and received a regular high school diploma'
        # else:
        #     display_data['high_school_choices'] = '12th grade and received a GED'
        #
        # if data_match['college_choices'] == 'less than 1 year college':
        #     display_data['college_choices'] = 'some college credit, but less than 1 year'
        # elif data_match['college_choices'] == 'more than 1 year college, no degree':
        #     display_data['college_choices'] = '1 or more years of college credit, but did not graduate with a degree'
        # elif data_match['college_choices'] == 'associates degree':
        #     display_data['college_choices'] = 'an Associate’s degree (for example: AA, AS)'
        # else:
        #     display_data['college_choices'] = 'a Bachelor’s degree (for example: BA, BS)'
        #
        # if data_match['after_bachelor_choices'] == 'masters degree':
        #     display_data['after_bachelor_choices'] = 'a Master’s degree (for example: MA, MS, MEng,MEd, MSW, MBA)'
        # elif data_match['after_bachelor_choices'] == 'professional degree':
        #     display_data['after_bachelor_choices'] = 'a Professional degree beyond a bachelor’s degree(for example: MD, DDS, DVM, LLB, JD)'
        # else:
        #     display_data['after_bachelor_choices'] = 'a Doctorate Degree (for example: PhD, EdD)'
        #
        # if data_match['highest_degree'] == 'no schooling':
        #     display_data['highest_degree'] = 'no schooling'
        # elif data_match['highest_degree'] == 'elementary or some secondary schooling':
        #     display_data['highest_degree'] = display_data['elementary_secondary_choices']
        # elif data_match['highest_degree'] == '12th grade no degree':
        #     display_data['highest_degree'] = '12th grade but did not receive a high school diploma'
        # elif data_match['highest_degree'] == 'high school graduate':
        #     display_data['highest_degree'] = display_data['high_school_choices']
        # elif data_match['highest_degree'] == 'college or some college':
        #     display_data['highest_degree'] = display_data['college_choices']
        # else:
        #     display_data['highest_degree'] = display_data['after_bachelor_choices']

        # if data_match['us_citizen_options'] == 'born usa':
        #     display_data['us_citizen_options'] = 'was born in the United States'
        # elif data_match['us_citizen_options'] == 'born us territory':
        #     display_data['us_citizen_options'] = 'was born in Puerto Rico, Guam, the U.S. Virgin Islands, or Northern Marianas'
        # elif data_match['us_citizen_options'] == 'born abroad us parents':
        #     display_data['us_citizen_options'] = 'was born abroad of a U.S. citizen parent or parents'
        # else:
        #     display_data['us_citizen_options'] = 'became a U.S. citizen by naturalization'
        #
        # if data_match['us_citizen'] == 1:
        #     display_data['us_citizen'] = 'a US citizen who ' + display_data['us_citizen_options']
        # else:
        #     display_data['us_citizen'] = 'not a US citizen'
        #
        # if data_match['political_party'] == 'democrat':
        #     display_data['political_party'] = 'a Democrat'
        # elif data_match['political_party'] == 'republican':
        #     display_data['political_party'] = 'a Republican'
        # elif data_match['political_party'] == 'independent':
        #     display_data['political_party'] = 'an Independent'
        # else:
        #     display_data['political_party'] = 'having no preference in regards to political party'
        #
        # if data_match['politcal_views'] == 0:
        #     display_data['politcal_views'] = 'extremely liberal'
        # elif data_match['politcal_views'] < 1 / 6 + 0.001:
        #     display_data['politcal_views'] = 'liberal'
        # elif data_match['politcal_views'] < 2 / 6 + 0.001:
        #     display_data['politcal_views'] = 'slightly liberal'
        # elif data_match['politcal_views'] < 3 / 6 + 0.001:
        #     display_data['politcal_views'] = 'moderate or middle of the road'
        # elif data_match['politcal_views'] < 4 / 6 + 0.001:
        #     display_data['politcal_views'] = 'slightly conservative'
        # elif data_match['politcal_views'] < 5 / 6 + 0.001:
        #     display_data['politcal_views'] = 'conservative'
        # else:
        #     display_data['politcal_views'] = 'extremely conservative'
        #
        # social_class_choices = [
        #     ['lower class', 'the Lower Class'],
        #     ['working class', 'the Working Class'],
        #     ['middle class', 'the Middle Class'],
        #     ['upper class', 'the Upper Class']
        #     ]
        #
        # for key, value in social_class_choices:
        #     if key == data_match['social_class']:
        #         display_data['social_class'] = value
        #
        # work_last_week_choices = [
        #     ['full time work', 'Working full time'],
        #     ['part time work', 'Working part time'],
        #     ['school', 'Studying'],
        #     ['housework', 'Keeping house']
        #     ]
        #
        # for key, value in work_last_week_choices:
        #     if key == data_match['work_last_week']:
        #         display_data['work_last_week'] = value.lower()

        # display_data['language'] = data_match['language'].capitalize()

        # if not restricted:
        #     if data_match['home'] == 'mobile home':
        #         display_data['home'] = 'mobile home'
        #     elif data_match['home'] == 'one family detached':
        #         display_data['home'] = 'one-family house detached from any other house'
        #     elif data_match['home'] == 'one family attached':
        #         display_data['home'] = 'one-family house attached to one or more houses'
        #     elif data_match['home'] == 'less than five apartment':
        #         display_data['home'] = 'unit in a building with less than 5 apartments'
        #     elif data_match['home'] == 'five or more apartments':
        #         display_data['home'] = 'unit in a building with 5 or more apartments'
        #     elif data_match['home'] == 'dorm':
        #         display_data['home'] = 'dormitory or hall of residence'
        #     elif data_match['home'] == 'boat':
        #         display_data['home'] = 'boat, RV, van etc.'
        #     else:
        #         display_data['home'] = data_match['home_other']
        #
        #     if data_match['guns'] == 0:
        #         display_data['guns'] = 'does not have any'
        #     else:
        #         display_data['guns'] = 'has some'
        #
        #     if data_match['place_growing_up'] == 'open country':
        #         display_data['place_growing_up'] = 'in open country but not on a farm'
        #     elif data_match['place_growing_up'] == 'farm':
        #         display_data['place_growing_up'] = 'on a farm'
        #     elif data_match['place_growing_up'] == 'small town':
        #         display_data['place_growing_up'] = 'in a small city or town (under 50,000)'
        #     elif data_match['place_growing_up'] == 'medium city':
        #         display_data['place_growing_up'] = 'in a medium-size city (50,000-250,000)'
        #     elif data_match['place_growing_up'] == 'suburb':
        #         display_data['place_growing_up'] = 'in a suburb near a large city'
        #     else:
        #         display_data['place_growing_up'] = 'in a large city (over 250,000)'
        #
        #     if data_match['employer'] == 'government employer':
        #         display_data['employer'] = ' works for the government or a public institution'
        #     elif data_match['employer'] == 'private business':
        #         display_data['employer'] = ' works for a private business or industry'
        #     elif data_match['employer'] == 'private non profit':
        #         display_data['employer'] = ' works for a private non-profit organization'
        #     else:
        #         display_data['employer'] = ' is self employed'
        #
        #     if data_match['work_tasks'] == 0:
        #         display_data['work_tasks'] = '1'
        #     elif data_match['work_tasks'] < 1 / 9 + 0.001:
        #         display_data['work_tasks'] = '2'
        #     elif data_match['work_tasks'] < 2 / 9 + 0.001:
        #         display_data['work_tasks'] = '3'
        #     elif data_match['work_tasks'] < 3 / 9 + 0.001:
        #         display_data['work_tasks'] = '4'
        #     elif data_match['work_tasks'] < 4 / 9 + 0.001:
        #         display_data['work_tasks'] = '5'
        #     elif data_match['work_tasks'] < 5 / 9 + 0.001:
        #         display_data['work_tasks'] = '6'
        #     elif data_match['work_tasks'] < 6 / 9 + 0.001:
        #         display_data['work_tasks'] = '7'
        #     elif data_match['work_tasks'] < 7 / 9 + 0.001:
        #         display_data['work_tasks'] = '8'
        #     elif data_match['work_tasks'] < 8 / 9 + 0.001:
        #         display_data['work_tasks'] = '9'
        #     else:
        #         display_data['work_tasks'] = '10'
        #
        #     if data_match['work_last_week'] == 'full time work':
        #         display_data['work_last_week'] = 'working full time. ' + display_data['Pronoun'] + display_data['employer'] + ' and describes ' + display_data['possessive'] + ' work tasks as a ' + display_data[
        #             'work_tasks'] + ' on a ten-point scale where 1 means mostly manual and 10 means mostly intellectual tasks'
        #     elif data_match['work_last_week'] == 'part time work':
        #         display_data['work_last_week'] = 'working part time. ' + display_data['Pronoun'] + display_data['employer'] + ' and describes ' + display_data['possessive'] + ' work tasks as a ' + display_data[
        #             'work_tasks'] + ' on a ten-point scale where 1 means mostly manual and 10 means mostly intellectual tasks'
        #     elif data_match['work_last_week'] == 'school':
        #         display_data['work_last_week'] = 'studying'
        #     else:
        #         display_data['work_last_week'] = 'keeping house outside of formal employment'
        #
        #     if data_match['work_last_week'] == 'full time work':
        #         '{m[pronoun]} {m[employer]} and describes {m[possessive]} work tasks as a {m[work_tasks] on a ten-point scale where 1 means mostly manual and 10 means mostly intellectual tasks'
        #
        #     if data_match['unemployed_10_years'] == 0:
        #         display_data['unemployed_10_years'] = 'has not'
        #     else:
        #         display_data['unemployed_10_years'] = 'has'
        #
        #     if data_match['labor_union'] == 0:
        #         display_data['labor_union'] = 'does not belong'
        #     else:
        #         display_data['labor_union'] = 'belongs'
        #
        #     if data_match['income_group_placement'] == 0:
        #         display_data['income_group_placement'] = 1
        #     elif data_match['income_group_placement'] < 1 / 9 + 0.001:
        #         display_data['income_group_placement'] = '2'
        #     elif data_match['income_group_placement'] < 2 / 9 + 0.001:
        #         display_data['income_group_placement'] = '3'
        #     elif data_match['income_group_placement'] < 3 / 9 + 0.001:
        #         display_data['income_group_placement'] = '4'
        #     elif data_match['income_group_placement'] < 4 / 9 + 0.001:
        #         display_data['income_group_placement'] = '5'
        #     elif data_match['income_group_placement'] < 5 / 9 + 0.001:
        #         display_data['income_group_placement'] = '6'
        #     elif data_match['income_group_placement'] < 6 / 9 + 0.001:
        #         display_data['income_group_placement'] = '7'
        #     elif data_match['income_group_placement'] < 7 / 9 + 0.001:
        #         display_data['income_group_placement'] = '8'
        #     elif data_match['income_group_placement'] < 8 / 9 + 0.001:
        #         display_data['income_group_placement'] = '9'
        #     else:
        #         display_data['income_group_placement'] = '10'
        #
        #     if data_match['social_class'] == 'lower class':
        #         display_data['social_class'] = 'the Lower Class'
        #     elif data_match['social_class'] == 'working class':
        #         display_data['social_class'] = 'the Working Class'
        #     elif data_match['social_class'] == 'middle class':
        #         display_data['social_class'] = 'the Middle Class'
        #     else:
        #         display_data['social_class'] = 'the Upper Class'
        #
        #     if data_match['financial_satisfaction'] == 1:
        #         display_data['financial_satisfaction'] = 'pretty well satisfied'
        #     elif data_match['financial_satisfaction'] == 1 / 2:
        #         display_data['financial_satisfaction'] = 'more or less satisfied'
        #     else:
        #         display_data['financial_satisfaction'] = 'not satisfied at all'
        #
        #     if data_match['parental_comparison_standards'] == 1:
        #         display_data['parental_comparison_standards'] = 'much better'
        #     elif data_match['parental_comparison_standards'] == 3 / 4:
        #         display_data['parental_comparison_standards'] = 'somewhat better'
        #     elif data_match['parental_comparison_standards'] == 2 / 4:
        #         display_data['parental_comparison_standards'] = 'about the same'
        #     elif data_match['parental_comparison_standards'] == 1 / 4:
        #         display_data['parental_comparison_standards'] = 'somewhat worse'
        #     else:
        #         display_data['parental_comparison_standards'] = 'much worse'
        #
        #     if data_match['sixteen_yo_comparison'] == 1:
        #         display_data['sixteen_yo_comparison'] = 'far above average'
        #     elif data_match['sixteen_yo_comparison'] == 3 / 4:
        #         display_data['sixteen_yo_comparison'] = 'above average'
        #     elif data_match['sixteen_yo_comparison'] == 2 / 4:
        #         display_data['sixteen_yo_comparison'] = 'average'
        #     elif data_match['sixteen_yo_comparison'] == 1 / 4:
        #         display_data['sixteen_yo_comparison'] = 'below average'
        #     else:
        #         display_data['sixteen_yo_comparison'] = 'far below average'
        #
        #     if data_match['american_pride'] == 1:
        #         display_data['american_pride'] = 'very proud'
        #     elif data_match['american_pride'] > 2 / 3:
        #         display_data['american_pride'] = 'quite proud'
        #     elif data_match['american_pride'] > 1 / 3:
        #         display_data['american_pride'] = 'not very proud'
        #     else:
        #         display_data['american_pride'] = 'not at all proud'
        #
        #     if data_match['importance_democracy'] == 0:
        #         display_data['importance_democracy'] = '1'
        #     elif data_match['importance_democracy'] < 1 / 9 + 0.001:
        #         display_data['importance_democracy'] = '2'
        #     elif data_match['importance_democracy'] < 2 / 9 + 0.001:
        #         display_data['importance_democracy'] = '3'
        #     elif data_match['importance_democracy'] < 3 / 9 + 0.001:
        #         display_data['importance_democracy'] = '4'
        #     elif data_match['importance_democracy'] < 4 / 9 + 0.001:
        #         display_data['importance_democracy'] = '5'
        #     elif data_match['importance_democracy'] < 5 / 9 + 0.001:
        #         display_data['importance_democracy'] = '6'
        #     elif data_match['importance_democracy'] < 6 / 9 + 0.001:
        #         display_data['importance_democracy'] = '7'
        #     elif data_match['importance_democracy'] < 7 / 9 + 0.001:
        #         display_data['importance_democracy'] = '8'
        #     elif data_match['importance_democracy'] < 8 / 9 + 0.001:
        #         display_data['importance_democracy'] = '9'
        #     else:
        #         display_data['importance_democracy'] = '10'
        #
        #     # Confidence in institutions programming. First loop through the institutions:
        #     # executive_branch_confidence
        #     # congress_confidence
        #     # supreme_court_confidence
        #     # military_confidence
        #     # police_confidence
        #     # banks_confidence
        #     # unions_confidence
        #     # public_ed_confidence
        #     # press_confidence
        #     # And group according to:
        #     #  0 'Hardly any confidence at all'
        #     #  1/2 'Only some confidence'
        #     #  1  'A great deal of confidence'
        #     # Then display below only the lines which are relevant with the associated institutions.
        #
        #     # Government Spending Priorities. First loop through the three priorities:
        #     # improve_condition_blacks
        #     # improve_condition_abroad
        #     # protecting_environment_abroad
        #     # And group according to:
        #     ################## Double check that I got the coding right below! #####################
        #     #  0 'Spending too little'
        #     #  1/2 'Spending the right amount'
        #     #  1  'Spending too much'
        #     # Then display below only the lines which are relevant with the associated priorities.
        #
        #     #           {m[Pronoun]} has a great deal of confidence in these institutions: {m[_confidence==1]}.
        #     #           {m[Pronoun]} has only some confidence in these institutions: {m[_confidence==1/2]}.
        #     #           {m[Pronoun]} has hardly any confidence at all in these institutions: {m[_confidence==0]}.
        #
        #     #           {m[Pronoun]} thinks that we are spending too much on: {m[_priorities==1]}.
        #     #           {m[Pronoun]} thinks that we are spending the right amount on: {m[_priorities==1/2]}.
        #     #           {m[Pronoun]} thinks that we are spending too little on: {m[_priorities==0]}.
        #
        #     if data_match['government_redistribution'] == 0:
        #         display_data['government_redistribution'] = '1'
        #     elif data_match['government_redistribution'] < 1 / 6 + 0.001:
        #         display_data['government_redistribution'] = '2'
        #     elif data_match['government_redistribution'] < 2 / 6 + 0.001:
        #         display_data['government_redistribution'] = '3'
        #     elif data_match['government_redistribution'] < 3 / 6 + 0.001:
        #         display_data['government_redistribution'] = '4'
        #     elif data_match['government_redistribution'] < 4 / 6 + 0.001:
        #         display_data['government_redistribution'] = '5'
        #     elif data_match['government_redistribution'] < 5 / 6 + 0.001:
        #         display_data['government_redistribution'] = '6'
        #     else:
        #         display_data['government_redistribution'] = '7'
        #
        #     if data_match['income_tax_level'] == 0:
        #         display_data['income_tax_level'] = 'too low'
        #     elif data_match['income_tax_level'] == 1 / 2:
        #         display_data['income_tax_level'] = 'about right'
        #     else:
        #         display_data['income_tax_level'] = 'too high'
        #
        #     if data_match['death_penalty'] == 0:
        #         display_data['death_penalty'] = 'opposes'
        #     else:
        #         display_data['death_penalty'] = 'favors'
        #
        #     if data_match['affirmative_action'] == 0:
        #         display_data['affirmative_action'] = 'strongly opposed to'
        #     elif data_match['affirmative_action'] < 1 / 3 + 0.001:
        #         display_data['affirmative_action'] = 'somewhat opposed to'
        #     elif data_match['affirmative_action'] < 2 / 3 + 0.001:
        #         display_data['affirmative_action'] = 'somewhat in favor of'
        #     else:
        #         display_data['affirmative_action'] = 'strongly in favor of'
        #
        #     if data_match['sex_before_marriage'] == 0:
        #         display_data['sex_before_marriage'] = 'always wrong'
        #     elif data_match['sex_before_marriage'] < 1 / 3 + 0.001:
        #         display_data['sex_before_marriage'] = 'almost always wrong'
        #     elif data_match['sex_before_marriage'] < 2 / 3 + 0.001:
        #         display_data['sex_before_marriage'] = 'wrong only sometimes'
        #     else:
        #         display_data['sex_before_marriage'] = 'not wrong at all'
        #
        #     if data_match['same_sex_relations'] == 0:
        #         display_data['same_sex_relations'] = 'always wrong'
        #     elif data_match['same_sex_relations'] < 1 / 3 + 0.001:
        #         display_data['same_sex_relations'] = 'almost always wrong'
        #     elif data_match['same_sex_relations'] < 2 / 3 + 0.001:
        #         display_data['same_sex_relations'] = 'wrong only sometimes'
        #     else:
        #         display_data['same_sex_relations'] = 'not wrong at all'
        #
        #     if data_match['abortion'] == 0:
        #         display_data['abortion'] = 'not be possible'
        #     else:
        #         display_data['abortion'] = 'be possible'
        #
        #     if data_match['people_helpful'] == 0:
        #         display_data['people_helpful'] = 'people are mostly just looking out for themselves'
        #     else:
        #         display_data['people_helpful'] = 'most of the time people try to be helpful'
        #
        #     if data_match['people_helpful'] == 0:
        #         display_data['people_helpful'] = 'people are mostly just looking out for themselves'
        #     else:
        #         display_data['people_helpful'] = 'most of the time people try to be helpful'
        #
        #     if data_match['people_take_advantage_of_you'] == 0:
        #         display_data['people_take_advantage_of_you'] = 'most people would try to be fair'
        #     else:
        #         display_data['people_take_advantage_of_you'] = 'most people would try to take advantage of you if they got a chance'
        #
        #     if data_match['people_trustworthy'] == 0:
        #         display_data['people_trustworthy'] = 'you cannot be too careful in dealing with people'
        #     else:
        #         display_data['people_trustworthy'] = 'most people can be trusted'
        #
        #     display[match] = display[match] + """When {m[pronoun]} was 16 years old, {m[pronoun]} lived {m[place_growing_up]}.
        #                                         Compared with families in general then, {m[possessive]} family's income was {m[sixteen_yo_comparison]}.
        #                                         {m[Pronoun]} spent the majority of last week {m[work_last_week]}.
        #                                         On a ten-point scale where a 1 is the lowest income group in America and a 10 is the highest, {m[pronoun]} views {m[reflexive]} in group {m[income_group_placement]}.
        #                                         {m[Pronoun]} views {m[reflexive]} as a member of the {m[social_class]}, is {m[financial_satisfaction]} with {m[possessive]} present financial situation, and views {m[possessive]} own standard of living now {m[parental_comparison_standards]} than {m[possessive]} parents when they were {m[possessive]} age.
        #                                         {m[Pronoun]} lives in a {m[home]}. {m[Pronoun]} {m[guns]} guns or revolvers in {m[possessive]} home.
        #                                         {m[Pronoun]} {m[unemployed_10_years]} been unemployed and looking for work for as long as month within the last ten years. {m[Pronoun]} {m[labor_union]} to a labor union.
        #                                         {m[Pronoun]} is {m[american_pride]} to live in America and views living in a country that is governed democratically as a {m[importance_democracy]} on a ten-point scale where 1 means it is “not at all important” and 10 means “absolutely important”.
        #                                         {m[Pronoun]} considers the amount of federal income tax we pay as {m[income_tax_level]}.
        #                                         {m[Pronoun]} thinks the government policy should be a {m[government_redistribution]} on a seven-point scale where 1 means means that the government ought to reduce the income differences between rich and poor and 10 means that the government should not concern itself with reducing income differences.
        #                                         {m[Pronoun]} {m[death_penalty]} the death penalty for persons convicted of murder.
        #                                         {m[Pronoun]} is {m[affirmative_action]} preferential hiring and promotion of African Americans.
        #                                         {m[Pronoun]} thinks that two consensual adults having sexual relations before marriage is {m[sex_before_marriage]}.
        #                                         {m[Pronoun]} thinks that two consensual adults of the same sex having sexual relations is {m[same_sex_relations]}.
        #                                         {m[Pronoun]} thinks that it should {m[abortion]} for a pregnant woman to obtain a legal abortion if the woman wants one for any reason.
        #                                         {m[Pronoun]} thinks that {m[people_helpful]}, {m[people_take_advantage_of_you]}, and {m[people_trustworthy]}.""".format(m=display_data)

        # if data_match['household_income'] == 0:
        #     display_data['household_income'] = 'under $1,000'
        # elif data_match['household_income'] == 1 / 24:
        #     display_data['household_income'] = 'between $1,000 and $2,999'
        # elif data_match['household_income'] == 2 / 24:
        #     display_data['household_income'] = 'between $3,000 and $3,999'
        # elif data_match['household_income'] == 3 / 24:
        #     display_data['household_income'] = 'between $4,000 and $4,999'
        # elif data_match['household_income'] == 4 / 24:
        #     display_data['household_income'] = 'between $5,000 and $5,999'
        # elif data_match['household_income'] == 5 / 24:
        #     display_data['household_income'] = 'between $6,000 and $6,999'
        # elif data_match['household_income'] == 6 / 24:
        #     display_data['household_income'] = 'between $7,000 and $7,999'
        # elif data_match['household_income'] == 7 / 24:
        #     display_data['household_income'] = 'between $8,000 and $9,999'
        # elif data_match['household_income'] == 8 / 24:
        #     display_data['household_income'] = 'between $10,000 and $12,499'
        # elif data_match['household_income'] == 9 / 24:
        #     display_data['household_income'] = 'between $12,500 and $14,999'
        # elif data_match['household_income'] == 10 / 24:
        #     display_data['household_income'] = 'between $15,000 and $17,499'
        # elif data_match['household_income'] == 11 / 24:
        #     display_data['household_income'] = 'between $17,500 and $19,999'
        # elif data_match['household_income'] == 12 / 24:
        #     display_data['household_income'] = 'between $20,000 and $22,499'
        # elif data_match['household_income'] == 13 / 24:
        #     display_data['household_income'] = 'between $22,500 and $24,999'
        # elif data_match['household_income'] == 14 / 24:
        #     display_data['household_income'] = 'between $25,000 and $29,999'
        # elif data_match['household_income'] == 15 / 24:
        #     display_data['household_income'] = 'between $30,000 and $34,999'
        # elif data_match['household_income'] == 16 / 24:
        #     display_data['household_income'] = 'between $35,000 and $39,999'
        # elif data_match['household_income'] == 17 / 24:
        #     display_data['household_income'] = 'between $40,000 and $49,999'
        # elif data_match['household_income'] == 18 / 24:
        #     display_data['household_income'] = 'between $50,000 and $59,999'
        # elif data_match['household_income'] == 19 / 24:
        #     display_data['household_income'] = 'between $60,000 and $74,999'
        # elif data_match['household_income'] == 20 / 24:
        #     display_data['household_income'] = 'between $75,000 and $89,999'
        # elif data_match['household_income'] == 21 / 24:
        #     display_data['household_income'] = 'between $90,000 and $109,999'
        # elif data_match['household_income'] == 22 / 24:
        #     display_data['household_income'] = 'between $110,000 and $129,999'
        # elif data_match['household_income'] == 23 / 24:
        #     display_data['household_income'] = 'between $130,000 and $149,999'
        # else:
        #     display_data['household_income'] = '$150,000 or more'

        # if data_match['children'] == 0:
        #     display_data['children'] = 'no children'
        # else:
        #     display_data['children'] = '{children_number} {child} and was {first_age} years old when '.format(
        #         children_number=int(data_match['children_number']),
        #         child='child' if data_match['children_number'] == 1 else 'children',
        #         first_age=int(data_match['children_first_age'])) + display_data[
        #                                    'possessive'] + ' first child was born'

    def display_matches(self, sequence):
        match_data = [
            dict(
                name=self.participant.vars['matches_names'][match],
                narrative=self.participant.vars['display'][match]
                )
            for match in sequence
            ]

        return match_data

    def determine_match_to_display(self, order):
        """
        Determines which match to display in a given round.
        Need to create the fields match_displayed = models.IntegerField() and match_displayed_name = models.StringField() in the models
        :return: a dict containing the match to show in this given round, and the associated name (e.g. Spade)
        """
        # round number is between 1 and max but the lists are between 0 and max-1
        number = self.round_number - 1
        # get which match this corresponds to
        match_to_show = self.participant.vars[order][number]
        match_name_to_show = self.participant.vars['matches_names'][match_to_show]

        # store in the database
        self.match_displayed = match_to_show
        self.match_displayed_name = match_name_to_show

        return {
            'match_to_show': match_to_show,
            'match_name_to_show': match_name_to_show
            }

    # store in the database which match has been displayed in a given round and what name it had
    match_displayed = models.IntegerField()
    match_displayed_name = models.StringField()

    # ask people to write a few words
    tweet = models.LongStringField(
        label="Write the first things that come to your mind about this participant (at least " + str(
            Constants.length_tweet) + " characters)"
        )

    def tweet_error_message(self, value):
        if len(value) < Constants.length_tweet:
            return "Please write at least " + str(Constants.length_tweet) + " characters. Note that the last character cannot be a space."
