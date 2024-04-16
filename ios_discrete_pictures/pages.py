from ios.pages import BaseIntro, BaseTask


class Intro(BaseIntro):
    pass


class Task(BaseTask):
    pass


page_sequence = [
    Intro,
    Task
    ]
