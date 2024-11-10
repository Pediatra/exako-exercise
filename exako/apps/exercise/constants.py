from enum import Enum, auto


class ExerciseType(int, Enum):
    ORDER_SENTENCE = auto()
    LISTEN_TERM = auto()
    LISTEN_TERM_MCHOICE = auto()
    LISTEN_SENTENCE = auto()
    SPEAK_TERM = auto()
    SPEAK_SENTENCE = auto()
    TERM_SENTENCE_MCHOICE = auto()
    TERM_DEFINITION_MCHOICE = auto()
    TERM_IMAGE_MCHOICE = auto()
    TERM_IMAGE_MCHOICE_TEXT = auto()
    TERM_CONNECTION = auto()
    RANDOM = auto()


class Level(Enum):
    BEGINNER = 'A1'
    ELEMENTARY = 'A2'
    INTERMEDIATE = 'B1'
    UPPER_INTERMEDIATE = 'B2'
    ADVANCED = 'C1'
    MASTER = 'C2'


class Language(str, Enum):
    ARABIC = 'ar'
    CHINESE_SIMPLIFIED = 'zh-CN'
    CHINESE_TRADITIONAL = 'zh-TW'
    ENGLISH_USA = 'en-US'
    ENGLISH_UK = 'en-GB'
    FRENCH = 'fr'
    GERMAN = 'de'
    ITALIAN = 'it'
    JAPANESE = 'ja'
    KOREAN = 'ko'
    POLISH = 'pl'
    PORTUGUESE_BRAZIL = 'pt-BR'
    PORTUGUESE_PORTUGAL = 'pt-PT'
    ROMANIAN = 'ro'
    RUSSIAN = 'ru'
    SPANISH = 'es'
    SPANISH_LATAM = 'es-419'
    SWEDISH = 'sv'
    TURKISH = 'tr'
    DUTCH = 'nl'
    GREEK = 'el'
    HINDI = 'hi'
    HEBREW = 'he'
    NORWEGIAN = 'no'
    DANISH = 'da'
    FINNISH = 'fi'
    CZECH = 'cs'
    HUNGARIAN = 'hu'
