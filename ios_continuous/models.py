author = 'Benjamin Beranek, Geoffrey Castillo'

doc = """
IOS measure, continuous.
"""

from ios.models import Constants as MetaConstants, MetaSubsession, MetaGroup, MetaPlayer


class Constants(MetaConstants):
    name_in_url = 'i_c'


class Subsession(MetaSubsession):
    @property
    def ios_type(self):
        return "'continuous'"

    @property
    def ios_pictures(self):
        return 'false'

    @property
    def ios_size(self):
        return 100


class Group(MetaGroup):
    pass


class Player(MetaPlayer):
    pass
