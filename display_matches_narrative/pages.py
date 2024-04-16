from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants


class Intro(Page):

    def vars_for_template(self):
        self.participant.vars['display'] = self.player.generate_display()
        display = self.player.display_matches(self.participant.vars['narrative_sequence'])

        return {
            'number_matches': Constants.num_rounds,
            'matches': display
            }


    def is_displayed(self):
        return self.round_number == 1


class Task(Page):
    form_model = 'player'
    form_fields = ['tweet']


    def vars_for_template(self):
        display = self.player.determine_match_to_display('narrative_sequence')

        return {
            'narrative': self.participant.vars['display'][display['match_to_show']],
            'name': display['match_name_to_show']
            }


page_sequence = [
    Intro,
    Task
    ]
