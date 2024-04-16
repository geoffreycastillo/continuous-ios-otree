# import the player of display_matches_narrative to use the function determining the order
from display_matches_narrative.models import Player as Player_narrative
from ._builtin import Page
from .models import Constants


class CommonIOS(Page):

    def vars_for_template(self):
        ios_type = self.subsession.ios_type
        ios_pictures = self.subsession.ios_pictures
        ios_size = self.subsession.ios_size
        ios_options = f"numberCircles: {ios_type}, " \
                      f"manyCircles: {ios_pictures}, " \
                      f"circleDiameter: {ios_size}"

        is_ios_continuous = True if ios_type == "'continuous'" else False
        is_ios_discrete = isinstance(ios_type, int)
        is_ios_pictures = True if ios_pictures == 'true' else False

        return {
            'number_matches': Constants.num_rounds,
            'is_ios_continuous': is_ios_continuous,
            'is_ios_discrete': is_ios_discrete,
            'is_ios_pictures': is_ios_pictures,
            'ios_pictures': ios_pictures,
            'ios_options': ios_options
            }


class BaseIntro(CommonIOS):
    template_name = 'ios/Intro.html'

    def is_displayed(self):
        return self.round_number == 1


class BaseTask(CommonIOS):
    template_name = 'ios/Task.html'
    form_model = 'player'
    form_fields = ['ios_distance', 'ios_overlap', 'ios_number']

    def vars_for_template(self):
        display = Player_narrative.determine_match_to_display(self.player, 'IOS_sequence')

        context = super().vars_for_template()
        addin = {
            'narrative': self.participant.vars['display'][display['match_to_show']],
            'name': display['match_name_to_show']
            }
        context.update(addin)

        return context
