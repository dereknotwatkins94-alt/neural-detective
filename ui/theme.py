STYLESHEET = """
QWidget { background: #0B0F14; color: #E8EDF2; font-size: 14px; }
QMainWindow { background: #0B0F14; }
QLabel { background: transparent; }
QLabel[kind="muted"] { color: #8D9AA8; font-size: 13px; }
QLabel[kind="eyebrow"] { color: #24B8A8; font-size: 12px; font-weight: 600; }
QLabel[kind="title"] { font-size: 28px; font-weight: 700; }
QLabel[kind="heading"] { font-size: 18px; font-weight: 600; }
QFrame#card { background: #111C24; border: 1px solid #23313C; border-radius: 12px; }
QFrame#sidebar { background: #0D151C; border-right: 1px solid #23313C; }
QFrame#topbar { background: #0E161D; border-bottom: 1px solid #23313C; }
QPushButton { background: #192630; border: 1px solid #293B46; border-radius: 8px; padding: 12px 18px; text-align: left; font-weight: 600; }
QPushButton:hover { background: #203642; border-color: #24B8A8; }
QPushButton:pressed { background: #144B4A; }
QPushButton:disabled { color: #66747F; background: #101A22; border-color: #202B34; }
QPushButton[primary="true"] { background: #12675F; border-color: #24B8A8; color: #F1FFFE; }
QPushButton[primary="true"]:hover { background: #18867A; }
QPushButton[primary="true"]:disabled { background: #101A22; color: #66747F; border-color: #202B34; }
QPushButton[nav="true"] { font-size: 13px; padding: 12px 10px; border: 1px solid transparent; background: transparent; font-weight: 500; }
QPushButton[nav="true"]:checked { background: #103439; border: 1px solid #1A6867; color: #57DED0; }
QPushButton[nav="true"]:hover { background: #162A34; }
QTextEdit, QLineEdit, QComboBox { background: #0C151D; border: 1px solid #293B46; border-radius: 8px; padding: 12px; selection-background-color: #12675F; }
QTextEdit:focus, QLineEdit:focus { border-color: #24B8A8; }
QProgressBar { background: #22313A; border: none; border-radius: 3px; max-height: 6px; }
QProgressBar::chunk { background: #24B8A8; border-radius: 3px; }
QProgressBar#stress::chunk { background: #DC5D62; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #101820; width: 7px; }
QScrollBar::handle:vertical { background: #30434E; border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QCheckBox { background: transparent; padding: 5px 0; spacing: 9px; }
QCheckBox:disabled { color: #66747F; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #47616C; border-radius: 4px; background: #0C151D; }
QCheckBox::indicator:checked { background: #24B8A8; border-color: #57DED0; }
QCheckBox::indicator:disabled { border-color: #293541; background: #101820; }
QToolTip { background: #192630; color: #E8EDF2; border: 1px solid #24B8A8; padding: 6px; }
"""
