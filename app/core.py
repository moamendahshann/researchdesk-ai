"""Page-aware ingestion and deterministic lexical retrieval."""
import io
import re
import unicodedata
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize(text):
    text = unicodedata.normalize('NFKC', text).lower()
    text = re.sub(r'[\u064b-\u065f\u0670\u0640]', '', text)
    return re.sub('[إأآ]', 'ا', text).replace('ى', 'ي')


def extract_pdf(data):
    if not data.startswith(b'%PDF-'):
        raise ValueError('Please upload a valid PDF file.')
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError('Encrypted PDFs are not supported. Upload an unlocked copy.')
        if len(reader.pages) > 200:
            raise ValueError('Maximum 200 pages per PDF.')
        pages = []
        empty = 0
        total = 0
        for number, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or '').strip()
            total += len(text)
            if total > 2_000_000:
                raise ValueError('Extracted text exceeds the document limit.')
            if not text:
                empty += 1
                continue
            words = text.split()
            for start in range(0, len(words), 180):
                chunk = ' '.join(words[start:start+220])
                if chunk:
                    pages.append({'page': number, 'text': chunk})
        if not pages:
            raise ValueError('No searchable text found. This PDF needs OCR before upload.')
        return pages, len(reader.pages), empty
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('Could not read this PDF. It may be damaged or unsupported.') from exc


def search(chunks, query, limit=5):
    if not chunks or not normalize(query).strip():
        return []
    vectorizer = TfidfVectorizer(preprocessor=normalize, token_pattern=r'(?u)\b\w+\b', ngram_range=(1,2), max_features=60000)
    try:
        matrix = vectorizer.fit_transform([c['text'] for c in chunks])
        q = vectorizer.transform([query])
    except ValueError:
        return []
    scores = cosine_similarity(q, matrix).ravel()
    order = scores.argsort()[::-1]
    return [{**chunks[int(i)], 'score': round(float(scores[i]), 4)} for i in order[:limit] if scores[i] > .015]
