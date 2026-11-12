"""python -m ml.train_model — обучение и оценка на отделённых шаблонах."""
import csv
import hashlib
import json
from pathlib import Path
import joblib
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from ml.contradiction_model import PairFeatures
from core.case_manager import ROOT

CLASSES = ['contradiction','consistent','unknown']


def train(output: Path | None = None) -> dict:
    directory = output or ROOT / 'ml/models'
    directory.mkdir(parents=True,exist_ok=True)
    dataset = ROOT/'ml/dataset.csv'
    with dataset.open(encoding='utf-8',newline='') as stream:
        rows = list(csv.DictReader(stream))
    training = [r for r in rows if r['split']=='train']
    testing = [r for r in rows if r['split']=='test']
    if {r['group'] for r in training} & {r['group'] for r in testing}:
        raise ValueError('Одна группа шаблонов попала в оба набора.')
    pipeline = Pipeline([('pair',PairFeatures()),('classifier',LogisticRegression(C=2.0,max_iter=1500,class_weight='balanced',random_state=17))])
    pipeline.fit([(r['a'],r['b']) for r in training],[r['label'] for r in training])
    expected = [r['label'] for r in testing]
    prediction = pipeline.predict([(r['a'],r['b']) for r in testing])
    report = classification_report(expected,prediction,labels=CLASSES,output_dict=True,zero_division=0)
    metrics = {'accuracy':accuracy_score(expected,prediction),'precision':report['macro avg']['precision'],
               'recall':report['macro avg']['recall'],'f1':report['macro avg']['f1-score'],
               'confusion_matrix':confusion_matrix(expected,prediction,labels=CLASSES).tolist(),'classes':CLASSES,'report':report,
               'train_size':len(training),'test_size':len(testing),'sklearn_version':sklearn.__version__,
               'dataset_sha256':hashlib.sha256(dataset.read_bytes()).hexdigest(),
               'note':'Синтетический учебный набор. Тестовые речевые шаблоны отделены от обучающих; перенос на произвольный язык ограничен.'}
    joblib.dump(pipeline,directory/'contradiction.joblib')
    (directory/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
    return metrics


if __name__=='__main__':
    print(json.dumps(train(),ensure_ascii=False,indent=2))
