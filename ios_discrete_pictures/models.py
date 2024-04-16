author = 'Benjamin Beranek, Geoffrey Castillo'

doc = """
IOS measure, discrete with pictures.
"""

from ios.models import Constants as MetaConstants, MetaSubsession, MetaGroup, MetaPlayer


class Constants(MetaConstants):
    name_in_url = 'i_d_p'


class Subsession(MetaSubsession):
    @property
    def ios_type(self):
        return 7

    @property
    def ios_pictures(self):
        return 'true'

    @property
    def ios_size(self):
        return 70


class Group(MetaGroup):
    pass


class Player(MetaPlayer):
    pass
