import json
from datetime import datetime
from PySide6.QtWidgets import QFrame, QVBoxLayout, QComboBox, QTextEdit
from ui.components.widgets import label, button
from core.case_manager import ROOT
from core.config import storage_dir


class MLPanel(QFrame):
    def __init__(self, engine, run_task, changed):
        super().__init__()
        self.setObjectName('card')
        self.engine = engine
        self.run_task = run_task
        self.changed = changed
        body = QVBoxLayout(self)
        body.setContentsMargins(22,20,22,20)
        body.addWidget(label('Лаборатория противоречий / ML','heading'))
        body.addWidget(label('TF-IDF + Logistic Regression. Модель может ошибаться: её вывод не подтверждает ложь и не определяет виновность.','muted'))
        self.selectors=[]
        self.inputs=[]
        for title in ('Утверждение А','Утверждение Б'):
            body.addWidget(label(title,'eyebrow'))
            selector = QComboBox()
            editor = QTextEdit()
            editor.setFixedHeight(86)
            editor.setPlaceholderText('Введите текст или выберите показание / изученную улику')
            selector.activated.connect(lambda index, combo=selector, entry=editor: entry.setPlainText(combo.itemData(index) or entry.toPlainText()))
            self.selectors.append(selector)
            self.inputs.append(editor)
            body.addWidget(selector)
            body.addWidget(editor)
        body.addWidget(button('Сравнить утверждения',self.analyze,'clue',True))
        self.result = label('')
        body.addWidget(self.result)
        self.metrics = label('','muted')
        body.addWidget(self.metrics)
        body.addWidget(button('Переобучить модель на локальном датасете',self.train,'resume'))
        self.refresh()
        self.show_metrics()

    def show_metrics(self, metrics=None):
        if metrics is None:
            path=storage_dir()/'ml/metrics.json'
            if not path.exists():
                path=ROOT/'ml/models/metrics.json'
            try:
                metrics=json.loads(path.read_text(encoding='utf-8'))
            except (OSError,ValueError):
                self.metrics.setText('Модель ещё не обучена. Нажмите «Переобучить».')
                return
        self.metrics.setText(f"Отложенный тест: {metrics['test_size']} пар · Accuracy {metrics['accuracy']:.0%} · Precision {metrics['precision']:.0%} · Recall {metrics['recall']:.0%} · F1 {metrics['f1']:.0%}.\nМатрица ошибок (строки — истина; столбцы — прогноз: противоречие / согласуется / недостаточно данных):\n"+'\n'.join('   '.join(map(str,row)) for row in metrics['confusion_matrix']))

    def refresh(self):
        material=[]
        for pid,messages in self.engine.session.dialogues.items():
            for m in messages:
                if m.speaker!='detective':
                    material.append((self.engine.people[pid]['name']+': '+m.text[:80],m.text))
        for slot in self.engine.evidence_slots():
            if slot['examined']:
                material.append((slot['title'],self.engine.evidence_detail(slot['id'])['description']))
        for combo in self.selectors:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem('Выбрать из материалов дела',None)
            for title,text in material:
                combo.addItem(title,text)
            combo.blockSignals(False)
        if self.engine.session.ml_results:
            last=self.engine.session.ml_results[-1]
            self.result.setText(f"{last['title']} · уверенность модели {last['confidence']:.0%}\nЭто гипотеза модели, а не подтверждённое противоречие сценария.")

    def analyze(self):
        a,b=(widget.toPlainText().strip() for widget in self.inputs)
        if not a or not b:
            self.result.setText('Заполните оба утверждения.')
            return
        def operation():
            from ml.contradiction_model import ContradictionModel
            return ContradictionModel().predict(a,b)
        def completed(result):
            result['time']=datetime.now().astimezone().isoformat(timespec='seconds')
            self.engine.session.ml_results.append(result)
            self.engine.session.journal.append(f"Гипотеза ML: {result['title']} ({result['confidence']:.0%}). А: {result['a']} Б: {result['b']}")
            self.changed()
        self.run_task('Модель сравнивает утверждения…',operation,completed)

    def train(self):
        def operation():
            from ml.train_model import train
            return train(storage_dir()/'ml')
        self.run_task('Обучение модели…',operation,self.show_metrics)
