from random import randint, choice

from otree.api import (
    models,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c
    )

author = 'Benjamin Beranek, Geoffrey Castillo'

doc = """
Filler task
"""


class Constants(BaseConstants):
    name_in_url = 'filler'
    players_per_group = None
    bound = 999
    num_questions = 10
    num_rounds = 1
    payment_per_question = c(0.10)
    timeout = 600


class Subsession(BaseSubsession):
    def creating_session(self):
        for player in self.get_players():
            player.participant.vars['filler'] = {}


class Group(BaseGroup):
    pass


def generate_answer_fields():
    return models.IntegerField(min=0, max=2 * Constants.bound)


def make_operation(operation, first_integer, second_integer):
    if operation == '+':
        result = first_integer + second_integer
    elif operation == '-':
        result = first_integer - second_integer

    return result


class Player(BasePlayer):

    def generate_task(self):
        bound = Constants.bound
        first_integer = randint(1, bound)
        second_integer = randint(1, bound)
        operation = choice(['+', '-'])
        result = make_operation(operation, first_integer, second_integer)
        while result <= 0:
            second_integer = randint(1, bound)
            result = make_operation(operation, first_integer, second_integer)

        return {
            'label': f"{first_integer} {operation} {second_integer} = ",
            'result': result
            }

    def start(self):
        self.participant.vars['filler']['tasks'] = [self.generate_task() for task in range(1, Constants.num_questions + 1)]

        num = 0
        for task in self.participant.vars['filler']['tasks']:
            setattr(self, f'target_{num}', task['result'])
            num += 1

    target_0 = generate_answer_fields()
    input_0 = generate_answer_fields()
    is_correct_0 = models.BooleanField()

    target_1 = generate_answer_fields()
    input_1 = generate_answer_fields()
    is_correct_1 = models.BooleanField()

    target_2 = generate_answer_fields()
    input_2 = generate_answer_fields()
    is_correct_2 = models.BooleanField()

    target_3 = generate_answer_fields()
    input_3 = generate_answer_fields()
    is_correct_3 = models.BooleanField()

    target_4 = generate_answer_fields()
    input_4 = generate_answer_fields()
    is_correct_4 = models.BooleanField()

    target_5 = generate_answer_fields()
    input_5 = generate_answer_fields()
    is_correct_5 = models.BooleanField()

    target_6 = generate_answer_fields()
    input_6 = generate_answer_fields()
    is_correct_6 = models.BooleanField()

    target_7 = generate_answer_fields()
    input_7 = generate_answer_fields()
    is_correct_7 = models.BooleanField()

    target_8 = generate_answer_fields()
    input_8 = generate_answer_fields()
    is_correct_8 = models.BooleanField()

    target_9 = generate_answer_fields()
    input_9 = generate_answer_fields()
    is_correct_9 = models.BooleanField()
