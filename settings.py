from os import environ

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

DEFAULT_HIT_SETTINGS = {
    'frame_height': 700,
    'expiration_hours': 7 * 24,  # 7 days
    'qualification_requirements': [
        # allow only US workers
        {
            'QualificationTypeId': "00000000000000000071",
            'Comparator': "EqualTo",
            'LocaleValues': [{'Country': "US"}]
            },
        # experienced mTurkers, completed HITS > 98%
        {
            'QualificationTypeId': "000000000000000000L0",
            'Comparator': "GreaterThanOrEqualTo",
            'IntegerValues': [98],
            },
        # reject people who already did the survey
        {
            'QualificationTypeId': "survey_qualification_ID", # replaced in production
            'Comparator': "DoesNotExist",
            },
        # reject people who already did the IOS + filler + IOS
        {
            'QualificationTypeId': "ios_qualification_ID", # replaced in production
            'Comparator': "DoesNotExist",
            },
        ]
    }

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 1.00,
    'participation_fee': 0.00,
    'doc': "",
    'mturk_hit_settings': DEFAULT_HIT_SETTINGS
    }

SESSION_CONFIG_IOS = {'num_demo_participants': 5,
                      'participation_fee': 0.5,
                      'compute_distance': True,
                      'matching_method': 'random',
                      'mturk_hit_settings': dict(
                          DEFAULT_HIT_SETTINGS,
                          grant_qualification_id='ios_qualification_ID', # replaced in production
                          title='Academic study',
                          minutes_allotted_per_assignment=40,
                          keywords=['bonus', 'study', 'survey'],
                          description='Short academic study, about 10 minutes long.',
                          template='global/mturk_template_ios_filler.html'),
                      'doc': """
IOS experiments (IOS version 1 > filler > IOS version 2)
"""
                      }

SESSION_CONFIGS = [
    {
        'name': 'survey',
        'display_name': "Survey",
        'num_demo_participants': 10,
        'app_sequence': [
            'intro',
            'survey',
            'outro'
            ],
        'compute_distance': False,
        'participation_fee': 1.25,
        'mturk_hit_settings': dict(
            DEFAULT_HIT_SETTINGS,
            grant_qualification_id='survey_qualification_ID', # replaced in production
            title='Academic survey',
            minutes_allotted_per_assignment=30,
            keywords=['bonus', 'study', 'survey'],
            description='Short academic survey, about 10 minutes long.',
            template='global/mturk_template_survey.html'),
        'doc': """
        Config for the construction of the database (no distance measure). 
        """
        },
    dict(SESSION_CONFIG_IOS,
         name='continuous_ios_pictorial_ios',
         display_name="Continuous IOS > Pictorial IOS",
         app_sequence=[
             'intro',
             'import_database',
             'survey',
             'display_matches_narrative',
             'ios_continuous',
             'filler',
             'ios_discrete_pictures',
             'outro'
             ],
         ),
    dict(SESSION_CONFIG_IOS,
         name='pictorial_ios_continuous_ios',
         display_name="Pictorial IOS > Continuous IOS",
         app_sequence=[
             'intro',
             'import_database',
             'survey',
             'display_matches_narrative',
             'ios_discrete_pictures',
             'filler',
             'ios_continuous',
             'outro'
             ],
         ),
    dict(SESSION_CONFIG_IOS,
         name='step_ios_pictorial_ios',
         display_name="Step-choice IOS > Pictorial IOS",
         app_sequence=[
             'intro',
             'import_database',
             'survey',
             'display_matches_narrative',
             'ios_discrete',
             'filler',
             'ios_discrete_pictures',
             'outro'
             ],
         ),
    dict(SESSION_CONFIG_IOS,
         name='pictorial_ios_step_ios',
         display_name="Pictorial IOS > Step-choice IOS",
         app_sequence=[
             'intro',
             'import_database',
             'survey',
             'display_matches_narrative',
             'ios_discrete_pictures',
             'filler',
             'ios_discrete',
             'outro'
             ],
         ),
    {
        'name': 'survey_only',
        'display_name': "[TEST] Only the survey [TEST]",
        'num_demo_participants': 5,
        'compute_distance': False,
        'app_sequence': [
            'survey'
            ],
        'doc': """
        """
        },
    {
        'name': 'import_survey_narrative_IOS',
        'display_name': "[TEST] Import database, survey, narrative display, IOS [TEST]",
        'num_demo_participants': 5,
        'compute_distance': True,
        'generate_display': True,
        'app_sequence': [
            'import_database',
            'survey',
            'display_matches_narrative',
            'ios_continuous'
            ],
        'doc': """
    """
        },
    {
        'name': 'import_survey_2_ios',
        'display_name': "[TEST] Import database, survey, narrative display, IOS and re-IOS [TEST]",
        'num_demo_participants': 5,
        'compute_distance': True,
        'transparency': False,
        'matching_method': 'random',
        'app_sequence': [
            'import_database',
            'survey',
            'display_matches_narrative',
            'ios_discrete_pictures',
            'ios_continuous',
            'ios_discrete',
            ],
        'doc': """
"""
        },
    {
        'name': 'intro_outro',
        'display_name': "[TEST] intro and outro only [TEST]",
        'num_demo_participants': 10,
        'test': True,
        'app_sequence': [
            'intro',
            'outro',
            ],
        'doc':
            """
            Only the intro and the outro
            """
        },
    {
        'name': 'filler_task',
        'display_name': "[TEST] filler task [TEST]",
        'num_demo_participants': 5,
        'test': True,
        'app_sequence': [
            'filler'
            ],
        'doc':
            """
            Filler task
            """
        },
    ]

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ROOMS = []

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

SECRET_KEY = 'secret_key' # changed in production

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree', 'localflavor', 'django_countries', 'bootstrap_datepicker_plus']

# mTurk config
AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')
