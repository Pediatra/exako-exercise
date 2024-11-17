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
    TERM_IMAGE_TEXT_MCHOICE = auto()
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
    CHINESE_SIMPLIFIED = 'zh-cn'
    CHINESE_TRADITIONAL = 'zh-tw'
    ENGLISH_USA = 'en-us'
    ENGLISH_UK = 'en-gb'
    FRENCH = 'fr'
    GERMAN = 'de'
    ITALIAN = 'it'
    JAPANESE = 'ja'
    KOREAN = 'ko'
    POLISH = 'pl'
    PORTUGUESE_BRAZIL = 'pt-br'
    PORTUGUESE_PORTUGAL = 'pt-pt'
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
