"""Обучаемая классификация пары. Вывод ML не устанавливает игровую истину."""
from pathlib import Path
import re
import joblib
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from core.case_manager import ROOT
from core.config import storage_dir

LABELS = {'contradiction':'Возможное противоречие', 'consistent':'Согласуется', 'unknown':'Недостаточно данных'}


def model_path() -> Path:
    custom = storage_dir() / 'ml/contradiction.joblib'
    return custom if custom.exists() else ROOT / 'ml/models/contradiction.joblib'


class PairFeatures(BaseEstimator, TransformerMixin):
    """Симметричное представление: |TFIDF(A)-TFIDF(B)|, произведение и признаки пары."""
    def fit(self, X, y=None):
        self.vectorizer_ = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), max_features=12000, sublinear_tf=True)
        self.vectorizer_.fit([text for pair in X for text in pair])
        return self

    @staticmethod
    def features(a: str, b: str) -> list[float]:
        a, b = a.lower().replace('ё','е'), b.lower().replace('ё','е')
        wa, wb = set(re.findall(r'\w+',a)), set(re.findall(r'\w+',b))
        overlap = len(wa & wb) / max(1, len(wa | wb))
        na = set(re.findall(r'\d{1,2}:\d{2}|\b\d+\b',a))
        nb = set(re.findall(r'\d{1,2}:\d{2}|\b\d+\b',b))
        neg = lambda s: bool(re.search(r'\b(?:не|нет|никогда|никто|нигде|ничего)\b',s))
        antonyms = [('закрыт','открыт'),('включ','выключ'),('один','вместе'),('пуст','полон'),('ушел','остал')]
        opposite = any((x in a and z in b) or (z in a and x in b) for x,z in antonyms)
        places = ('кабинет','библиотек','кухн','гараж','гостин','двор','пост','склад','террас','парк','холл','зал')
        pa, pb = {p for p in places if p in a}, {p for p in places if p in b}
        return [overlap,float(neg(a)!=neg(b)),float(bool(na & nb)),float(bool(na and nb and not na & nb)),
                float(bool(pa and pb and not pa & pb)),float(opposite),float(a==b),float(bool(wa & wb)),float(bool(na and nb))]

    def transform(self, X):
        left = self.vectorizer_.transform([p[0] for p in X])
        right = self.vectorizer_.transform([p[1] for p in X])
        difference = left-right
        difference.data = np.abs(difference.data)
        numeric = csr_matrix(np.array([self.features(*pair) for pair in X], dtype=float))
        return hstack([difference,left.multiply(right),numeric],format='csr')


class ContradictionModel:
    def __init__(self, path: Path | None = None):
        self.path = path or model_path()
        import json
        import sklearn
        metadata=self.path.with_name('metrics.json')
        if metadata.exists():
            version=json.loads(metadata.read_text(encoding='utf-8')).get('sklearn_version')
            if version!=sklearn.__version__:
                from ml.train_model import train
                train(storage_dir()/'ml')
                self.path=storage_dir()/'ml/contradiction.joblib'
        self.pipeline = joblib.load(self.path)

    def predict(self, a: str, b: str) -> dict:
        if not a.strip() or not b.strip():
            raise ValueError('Введите оба утверждения.')
        probabilities = self.pipeline.predict_proba([(a[:4000],b[:4000])])[0]
        index = int(np.argmax(probabilities))
        category = str(self.pipeline.classes_[index])
        return {'label':category,'title':LABELS[category],'confidence':float(probabilities[index]),
                'probabilities':{str(c):float(p) for c,p in zip(self.pipeline.classes_,probabilities)},'a':a[:4000],'b':b[:4000]}
