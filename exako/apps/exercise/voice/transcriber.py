import json
import wave

from fastapi import HTTPException, status
from vosk import KaldiRecognizer, Model

from exako.apps.exercise.voice.text import text_speak_time
from exako.core.constants import Language
from exako.settings import BASE_DIR

en_model_path = BASE_DIR / 'exako/apps/exercise/voice/models/en-model'

language_model_map = {
    Language.ENGLISH_USA: en_model_path,
    Language.ENGLISH_UK: en_model_path,
}


def trascribe_to_text(
    audio_file: bytes,
    vocabulary: list[str],
    language: Language,
):
    try:
        with wave.open(audio_file, 'rb') as wf:
            if (
                wf.getnchannels() != 1
                or wf.getsampwidth() != 2
                or wf.getcomptype() != 'NONE'
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='audio file must be WAV format mono PCM.',
                )

            audio_size = wf.getnframes() / wf.getframerate()
            if audio_size > text_speak_time(' '.join(vocabulary)):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail='audio_file is too big.',
                )

            model_path = language_model_map.get(language)
            model = Model(model_path=model_path)
            recognizer = KaldiRecognizer(
                model,
                wf.getframerate(),
                json.dumps(vocabulary),
            )

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break

        final_result = json.loads(recognizer.FinalResult())
        text = final_result.get('text', '')
        if text == '':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='could not trascribe text.',
            )
        return text
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='something went wrong in audio_file transcription.',
        )
