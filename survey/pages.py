# get the IP
from ipware import get_client_ip

from ._builtin import Page


# treat zipcodes

# to convert the date-of-birth string into datetime


# needed if we want the progress bar
class ProgressBarPage(Page):
    def vars_for_template(self):
        return {
            'total_page': total_pages,
            'current_page': current_page(self),
            }


class Intro(Page):
    pass


class Part1(ProgressBarPage):
    # replace by class Part1(ProgressBarPage): for the progress bar
    """ Contains the questions of Demographics, RaceEthnicityReligion, Origin """
    form_model = 'player'
    form_fields = ['sex', 'date', 'marital', 'children', 'children_number', 'children_first_age', 'language',
                   'language_other', 'zip', 'ethnicity', 'ethnicity_choice', 'ethnicity_choice_other', 'race',
                   'race_indian_other', 'race_asian_other', 'race_islander_other', 'race_other', 'religion',
                   'religion_denomination', 'religion_denomination_other', 'country_growing_up', 'us_state_grow_up',
                   'another_country_grow_up', 'us_citizen', 'us_citizen_options']

    def error_message(self, values):
        if values['children'] and values['children_number'] is None:
            return "Please enter how many children you have had."
        if values['children'] and values['children_first_age'] is None:
            return "Please enter how old you were when your first child was born."
        if values['ethnicity'] and values['ethnicity_choice'] is None:
            return "You have indicated that you are of Hispanic, Latino, or Spanish origin, but you have not selected your ethnicity."
        if values['ethnicity'] and values['ethnicity_choice'] == 'other' and values['ethnicity_choice_other'] is None:
            return "You have indicated that your ethnicity is 'Another Hispanic, Latino, or Spanish origin' but you have not entered which one."
        if values['race'] == 'american indian' and values['race_indian_other'] is None:
            return "You have indicated that your race is 'American Indian or Alaska Native' but you have not entered the name of your enrolled or principal tribe."
        if values['race'] == 'other asian' and values['race_asian_other'] is None:
            return "You have indicated that your race is 'Other Asian' but you have not entered which one."
        if values['race'] == 'other pacific' and values['race_islander_other'] is None:
            return "You have indicated that your race is 'Other Pacific Islander' but you have not entered which one."
        if values['race'] == 'other' and values['race_other'] is None:
            return "You have indicated that your race is 'Some other race' but you have not entered which one."
        if values['religion'] and values['religion_denomination'] is None:
            return "You have indicated that you belong to a religious denomination but you have not selected which one."
        if values['religion'] and values['religion_denomination'] == 'other' and values[
            'religion_denomination_other'] is None:
            return "You have indicated that you belong to 'Other denomination' but you have not entered which one."
        if values['language'] == 'other' and values['language_other'] is None:
            return "You have indicated that you normally speak another language at home but you have not entered which one."
        if values['country_growing_up'] == 'usa' and values['us_state_grow_up'] is None:
            return "You have indicated that you grew up in the USA but you have not selected the US State or Territory in which you grew up."
        if values['country_growing_up'] == 'another country' and values['another_country_grow_up'] is None:
            return "You have indicated that you grew up in another country but you have not selected the country in which you grew up."
        if values['us_citizen'] and values['us_citizen_options'] is None:
            return "You have indicated that you are a US citizen but you have not selected how you are a citizen."

    def before_next_page(self):
        self.player.find_lat_long()


class Part2(ProgressBarPage):
    """ Contains the questions of HomeEducation, Work,  Economic """
    form_model = 'player'
    form_fields = ['home', 'home_other', 'guns', 'place_growing_up', 'highest_degree', 'elementary_secondary_choices',
                   'high_school_choices', 'college_choices', 'after_bachelor_choices',
                   'elementary_secondary_choices_incomplete_high_school', 'major_college', 'major_bachelor',
                   'work_last_week', 'profession', 'employer', 'work_tasks', 'unemployed_10_years', 'labor_union',
                   'household_income', 'income_group_placement', 'sixteen_yo_comparison',
                   'parental_comparison_standards', 'social_class', 'financial_satisfaction']

    """ Questions for Geoffrey: Can we specify the requirements for elementary_secondary_choices_incomplete_high_school above to be an integer between 1 and 11?"""

    def error_message(self, values):
        if values['home'] == 'other' and values['home_other'] is None:
            return "You have indicated that 'other' best describes the building where you live but you have not entered which one."
        if values['highest_degree'] == 'elementary or some secondary schooling' and values[
            'elementary_secondary_choices'] is None:
            return "You have indicated that the level of school you have completed is between first and eleventh grade but you have not specified which one."
        if values['highest_degree'] == 'elementary or some secondary schooling' and values[
            'elementary_secondary_choices'] == 'incomplete high school' and values[
            'elementary_secondary_choices_incomplete_high_school'] is None:
            return "You have indicated that the highest degree or level of school you have completed is 'Grade 1 through 11' but you have not entered the grade."
        if values['highest_degree'] == 'elementary or some secondary schooling' and values[
            'elementary_secondary_choices'] == 'incomplete high school' and values[
            'elementary_secondary_choices_incomplete_high_school'] is not None and values[
            'elementary_secondary_choices_incomplete_high_school'] < 1:
            return "You have indicated that the highest degree or level of school you have completed is 'Grade 1 through 11' but you have not entered at least 1."
        if values['highest_degree'] == 'high school graduate' and values['high_school_choices'] is None:
            return "You have indicated that the highest degree or level of school you have completed is 'High school graduate' but you have not selected which one."
        if values['highest_degree'] == 'college or some college' and values['college_choices'] is None:
            return "You have indicated that the highest degree or level of school you have completed is 'College or some college' but you have not selected which one."
        if values['highest_degree'] == 'beyond bachelors' and values['after_bachelor_choices'] is None:
            return "You have indicated that the highest degree or level of school you have completed is some sort of 'Postgraduate education' but you have not selected which one."
        if values['highest_degree'] == 'college or some college' and values['major_college'] is None:
            return "You have indicated that you have completed 'College or some college' but you have not specified your major."
        if values['highest_degree'] == 'beyond bachelors' and values['major_bachelor'] is None:
            return "You have indicated that you have completed some sort of 'Postgraduate education' but you have not specified your major."
        if values['work_last_week'] == 'full time work' and values['profession'] is None:
            return "You have indicated that you were 'Working full time' for the majority of last week but you have not written what your profession is."
        if values['work_last_week'] == 'part time work' and values['profession'] is None:
            return "You have indicated that you were 'Working part time' for the majority of last week but you have not written what your profession is."
        if values['work_last_week'] == 'full time work' and values['employer'] is None:
            return "You have indicated that you were 'Working full time' for the majority of last week but you have not selected a category to describe your employer."
        if values['work_last_week'] == 'part time work' and values['employer'] is None:
            return "You have indicated that you were 'Working part time' for the majority of last week but you have not selected a category to describe your employer."
        if values['work_last_week'] == 'full time work' and values['work_tasks'] is None:
            return "You have indicated that you were 'Working full time' for the majority of last week but you have not described your work tasks as mostly manual or mostly intellectual."
        if values['work_last_week'] == 'part time work' and values['work_tasks'] is None:
            return "You have indicated that you were 'Working part time' for the majority of last week but you have not described your work tasks as mostly manual or mostly intellectual."


class Part3(ProgressBarPage):
    """ Contains the questions of NatioGovernance, PoliticalViews,  Confidence """
    form_model = 'player'
    form_fields = ['importance_democracy', 'american_pride', 'political_party', 'other_political_party',
                   'politcal_views', 'executive_branch_confidence', 'congress_confidence', 'supreme_court_confidence',
                   'military_confidence', 'police_confidence', 'banks_confidence', 'unions_confidence',
                   'public_ed_confidence', 'press_confidence']

    def error_message(self, values):
        if values['political_party'] == 'other party' and values['other_political_party'] is None:
            return "You have indicated that you think of yourself as a member of an 'Other party' but you have not entered the other political party you identify with."


class Part4(ProgressBarPage):
    """ Contains the questions of Priorities, RaceAffirmative,  Sex, PerceptionOthers """
    form_model = 'player'
    form_fields = ['improve_condition_blacks', 'improve_condition_abroad', 'protecting_environment',
                   'government_redistribution', 'income_tax_level', 'death_penalty', 'affirmative_action',
                   'sex_before_marriage', 'same_sex_relations', 'abortion', 'people_helpful',
                   'people_take_advantage_of_you', 'people_trustworthy']

    def before_next_page(self):
        # get the IP and store it in the database
        ip, is_routable = get_client_ip(self.request)
        if ip is None:
            self.player.ip = "Unable to get IP address"
        else:
            # We got the client's IP address
            if is_routable:
                # The client's IP address is publicly routable on the Internet
                self.player.ip = ip
            else:
                self.player.ip = "IP is private"

        if self.session.config['compute_distance']:
            # create distance table
            self.participant.vars['distance_table'] = self.player.create_distances_table()
            # compute distances
            self.player.compute_distances(self.participant.vars['distance_table'])
            # find the matches
            self.participant.vars['matches'] = self.player.find_matches()
            # pass data of the matched participants
            self.player.pass_data_matched_participants(self.participant.vars['distance_table'], self.participant.vars['matches'])


page_sequence = [
    Intro,
    Part1,
    Part2,
    Part3,
    Part4
    ]

# total number of pages minus the intro
total_pages = len(page_sequence) - 1


# current page number
def current_page(self):
    # page_sequence.index(type(self)) starts at 0 but the intro is already 0 so no need to add 1
    page_number = page_sequence.index(type(self))
    return page_number


all_fields = Part1.form_fields + Part2.form_fields + Part3.form_fields + Part4.form_fields
