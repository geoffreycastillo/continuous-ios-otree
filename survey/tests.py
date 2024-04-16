from otree.api import Currency as c, currency_range
from . import pages
from ._builtin import Bot
from .models import Constants

from .models import Player as models_Player

import string

# treat zipcodes
import zipcodes

import random


class PlayerBot(Bot):

    def play_round(self):

        def random_answer(self, page):
            """"
            Random answers to all fields in a page
            :param page: the page object where the fields are, e.g. pages.Part1
            :return a dict of answers for this page
            """
            answers = {}
            fields = page.form_fields
            for field in fields:

                object = models_Player._meta.get_field(field)
                # print("---------------------")
                # print("Field object is:", object)

                choices = object.choices
                # if choices is not empty we use some of it

                if choices:
                    # print("Choices are provided")
                    choices_length_0 = len(choices) - 1
                    choice_number = random.randint(0, choices_length_0)
                    answer = choices[choice_number][0]

                else:
                    # print("Choices are not provided")
                    type = object.get_internal_type()
                    # print("The type is:", type)

                    if type == 'FloatField' or type == 'IntegerField':
                        # print("It is a int or a float")
                        min = object.min if object.min is not None else random.randint(0, 100)
                        max = object.max if object.max is not None else random.randint(min, 100)
                        # print("Min is", min, "and max is", max)
                        if type == 'IntegerField':
                            answer = random.randint(min, max)
                        else:
                            answer = random.uniform(min, max)

                    if type == "CharField":
                        # print("It is a string")
                        # get a  random string
                        length = random.randint(1, 10)
                        answer = ''.join(random.choices(string.ascii_lowercase, k=length))

                    if type == "BooleanField":
                        answer = random.choice([True, False])

                # print("My answer will be:", answer)
                answers[field] = answer

            return answers


        yield pages.Intro

        answers = random_answer(self, pages.Part1)
        answers["date"] = "07/25/1989"

        good_zip = False
        while good_zip is False:
            random_zipcode = random.randint(00000, 99999)
            random_zipcode = str(random_zipcode)
            # print("Random zipcode is", random_zipcode)
            good_zip = zipcodes.is_real(random_zipcode)
            # print("Is it a good zip?", good_zip)
        answers["zip"] = random_zipcode
        # print("answers dict is:", answers)

        yield pages.Part1, answers

        answers = random_answer(self, pages.Part2)

        yield pages.Part2, answers

        answers = random_answer(self, pages.Part3)

        yield pages.Part3, answers

        answers = random_answer(self, pages.Part4)

        yield pages.Part4, answers

        pass
