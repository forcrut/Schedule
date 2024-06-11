import os


class Config:
    print(os.path.join(os.path.dirname(__file__)))

    DATABASES_PATH = os.path.join(os.path.dirname(__file__), 'dbs')
    os.environ['DATABASES_PATH'] = DATABASES_PATH
    DEFAULT_TEACHER_IMAGE = 'default.webp'
    os.environ['DEFAULT_TEACHER_IMAGE'] = DEFAULT_TEACHER_IMAGE
    DEFAULT_ENCLOSURE_IMAGE = 'default_building.png'
    os.environ['DEFAULT_ENCLOSURE_IMAGE'] = DEFAULT_ENCLOSURE_IMAGE

    @classmethod
    def validate(cls):
        if not os.path.exists(cls.DATABASES_PATH):
            raise Exception(f"Directory /dbs is not found")
        elif not os.path.exists(os.path.join(os.path.dirname(__file__) + '/static/images', cls.DEFAULT_TEACHER_IMAGE)):
            raise Exception(f"Default teacher image({cls.DEFAULT_TEACHER_IMAGE}) is not found")
        elif not os.path.exists(os.path.join(os.path.dirname(__file__) + '/static/images', cls.DEFAULT_ENCLOSURE_IMAGE)):
            raise Exception(f"Default building image({cls.DEFAULT_ENCLOSURE_IMAGE}) is not found")

Config.validate()
