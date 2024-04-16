from ._builtin import Page
from .models import Constants


class Intro(Page):
    def vars_for_template(self):
        return {
            'timeout': Constants.timeout / 60
            }


class Task(Page):
    form_model = 'player'
    form_fields = ['input_' + str(num) for num in range(Constants.num_questions)]
    timeout_seconds = Constants.timeout

    def vars_for_template(self):
        labels_and_fields = [
            {'label': task['label'],
             'field': field
             } for task, field in zip(self.participant.vars['filler']['tasks'], self.form_fields)
            ]

        return {
            'labels_and_fields': labels_and_fields,
            'field_min': 0,
            'field_max': 2 * Constants.bound,
            }

    def before_next_page(self):
        self.participant.vars['filler']['boolean_list'] = []
        for i in range(Constants.num_questions):
            input_field = f'input_{i}'
            target_field = f'target_{i}'
            boolean_field = f'is_correct_{i}'
            bool = getattr(self.player, input_field) == getattr(self.player, target_field)
            setattr(self.player, boolean_field, bool)
            self.participant.vars['filler']['boolean_list'].append(bool)
            if bool:
                self.player.payoff += Constants.payment_per_question


class Result(Page):
    form_model = 'player'

    def vars_for_template(self):
        labels_and_fields = [
            {'label': task['label'],
             'field': field,
             'value': getattr(self.player, field),
             'bool': bool
             } for task, field, bool in zip(self.participant.vars['filler']['tasks'], Task.form_fields, self.participant.vars['filler']['boolean_list'])
            ]

        return {
            'labels_and_fields': labels_and_fields,
            'field_min': 0,
            'field_max': 2 * Constants.bound,
            }


page_sequence = [Intro, Task, Result]
