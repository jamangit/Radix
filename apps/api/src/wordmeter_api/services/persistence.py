import uuid
from collections import Counter

from sqlalchemy.orm import Session

from wordmeter_api.analysis import AnalysisResult
from wordmeter_api.db.models import Analysis, AnalysisWord

MAX_WORD_LENGTH = 100


def save_analysis(
    session: Session, user_id: uuid.UUID, result: AnalysisResult, counts: Counter[str]
) -> None:
    if result.total_words == 0:
        return
    session.add(
        Analysis(
            user_id=user_id,
            language=result.language,
            total_words=result.total_words,
            unique_words=result.unique_words,
            words=[
                AnalysisWord(word=word, count=count)
                for word, count in counts.items()
                if len(word) <= MAX_WORD_LENGTH
            ],
        )
    )
    session.commit()
