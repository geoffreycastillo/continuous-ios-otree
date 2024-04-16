author = 'Benjamin Beranek, Geoffrey Castillo'

doc = """
IOS measure.
"""

# to shuffle the lists
import random

from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer
    )

# import the constants of the distance measure so that we can get the number of matches
from import_database.models import Constants as database_vars


class Constants(BaseConstants):
    name_in_url = 'i'
    players_per_group = None
    num_rounds = database_vars.number_matches
    sequence = list(range(num_rounds))


class MetaSubsession(BaseSubsession):

    def creating_session(self):
        # only do this in the first round
        if self.round_number == 1:
            for player in self.get_players():
                player.participant.vars['IOS_sequence'] = player.determine_order()

    class Meta:
        abstract = True


class MetaGroup(BaseGroup):
    class Meta:
        abstract = True


class MetaPlayer(BasePlayer):

    def determine_order(self):
        """"
        Randomises order of IOS
        We don't randomise the matches_name as we need to keep the same association as in the narrative display
        :return shuffled order
        """
        sequence = Constants.sequence.copy()
        random.shuffle(sequence)

        return sequence

    def start(self):
        self.ios_type = str(self.subsession.ios_type)

    # store in the database which match has been displayed in a given round and what name it had
    match_displayed = models.IntegerField()
    match_displayed_name = models.StringField()

    # store IOS data
    ios_distance = models.FloatField()
    ios_overlap = models.FloatField()
    ios_number = models.IntegerField(blank=True)
    ios_type = models.StringField()

    class Meta:
        abstract = True


class Subsession(MetaSubsession):
    pass


class Group(MetaGroup):
    pass


class Player(MetaPlayer):
    pass
