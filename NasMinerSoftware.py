import sys
import os
import json
import platform
import subprocess
import psutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QTabWidget, QSlider, QTextEdit, QFrame, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


CONFIG_FILE = "config.json"
LOGO_PATH = "img"
CRYPTO_LIST = {
    "LTC": "LbiyhmetYUJ1FRHJQ7p1sXqaQLCugG65Yh",
    "ETH": "0x3934B84B4E4Fd7caF90730eEB72f8457bffa9deE",
    "BNB": "0x3934B84B4E4Fd7caF90730eEB72f8457bffa9deE",
    "SOL": "H6WrvQDiXJc4dZEidN35ma5A6mzCz6xzBDhCeUndTM6W"
}

RATE_ESTIMATE = {
    "LTC": 0.00002,
    "ETH": 0.00001,
    "BNB": 0.00003,
    "SOL": 0.00005
}

def is_windows():
    return platform.system() == "Windows"

def get_xmrig_cmd(coin, wallet, worker, threads):
    xmrig_path = "nasminer.exe" if is_windows() else "./nasminer"
    url = "rx.unmineable.com:3333"
    algo = "rx"
    full = f"{coin}:{wallet}.{worker}"
    return [xmrig_path, "-a", algo, "-o", url, "-u", full, "-p", "x", "-k", "--threads", str(threads)], full

def load_wallets():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(CRYPTO_LIST, f, indent=4)
        return CRYPTO_LIST.copy()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(CONFIG_FILE, "w") as f:
        json.dump(wallets, f, indent=4)

class MinerThread(QThread):
    new_log = pyqtSignal(str)
    share_accepted = pyqtSignal(str)

    def __init__(self, cmd, coin):
        super().__init__()
        self.cmd = cmd
        self.coin = coin
        self._running = True

    def run(self):
        try:
            process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while self._running:
                line = process.stdout.readline()
                if not line:
                    break
                # Masquage du pool dans les logs
                line_filtered = line.strip().replace("rx.unmineable.com", "NASMINER.POOL")
                self.new_log.emit(line_filtered)
                if "accepted" in line_filtered.lower():
                    self.share_accepted.emit(self.coin)
        except Exception as e:
            self.new_log.emit(f"[ERREUR] {e}")

    def stop(self):
        self._running = False
        self.terminate()

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.data_x = []
        self.data_cpu = []
        self.data_ram = []

    def update_plot(self, x, cpu, ram):
        self.data_x.append(x)
        self.data_cpu.append(cpu)
        self.data_ram.append(ram)
        if len(self.data_x) > 50:
            self.data_x.pop(0)
            self.data_cpu.pop(0)
            self.data_ram.pop(0)

        self.ax.clear()
        self.ax.plot(self.data_x, self.data_cpu, label="CPU %", color="#ff4444")
        self.ax.plot(self.data_x, self.data_ram, label="RAM %", color="#ffaa00")
        self.ax.set_ylim(0, 100)
        self.ax.legend()
        self.ax.set_title("Consommation CPU & RAM")
        self.draw()

class NasMinerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.wallets = load_wallets()
        self.threads = 1
        self.mining_threads = []
        self.accepted_shares = 0
        self.mined_crypto = {coin: 0.0 for coin in CRYPTO_LIST.keys()}
        self.init_ui()
        self.update_stats()
        self.show()

    def init_ui(self):
        self.setWindowTitle("NasMiner PRO")
        self.setGeometry(100, 100, 950, 700)
        self.setStyleSheet("background-color: #0d0d0d; color: white; font-family: Consolas;")

        # Onglets
        self.tabs = QTabWidget(self)
        self.tabs.setGeometry(10, 10, 930, 680)
        self.tabs.setStyleSheet("""
            QTabBar::tab {background: #220000; color: #ff4444; padding: 10px; font-weight: bold;}
            QTabBar::tab:selected {background: #990000; color: white;}
        """)

        self.tab_mining = QWidget()
        self.tab_stats = QWidget()
        self.tab_config = QWidget()

        self.tabs.addTab(self.tab_mining, "Minage")
        self.tabs.addTab(self.tab_stats, "Statistiques")
        self.tabs.addTab(self.tab_config, "Configuration")

        self.setup_tab_mining()
        self.setup_tab_stats()
        self.setup_tab_config()

    def setup_tab_mining(self):
        layout = QVBoxLayout()
        # Crypto selection avec logos
        logo_layout = QHBoxLayout()

        self.coin_buttons = {}
        for coin in self.wallets.keys():
            pixmap = QPixmap(os.path.join(LOGO_PATH, f"{coin}.png")).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            btn = QPushButton()
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(pixmap.size())
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {border: 2px solid #660000; background-color: #220000;}
                QPushButton:checked {border: 3px solid #ff4444; background-color: #440000;}
            """)
            btn.clicked.connect(lambda _, c=coin: self.select_coin(c))
            self.coin_buttons[coin] = btn
            logo_layout.addWidget(btn)

        layout.addLayout(logo_layout)

        self.selected_coin = list(self.wallets.keys())[0]
        self.coin_buttons[self.selected_coin].setChecked(True)

        # Wallet & Worker input
        form_layout = QHBoxLayout()
        form_left = QVBoxLayout()
        form_right = QVBoxLayout()

        lbl_wallet = QLabel("Adresse Wallet :")
        self.input_wallet = QLineEdit(self.wallets[self.selected_coin])
        self.input_wallet.setStyleSheet("background-color: #1a1a1a; color: #ff4444; padding: 5px;")
        form_left.addWidget(lbl_wallet)
        form_left.addWidget(self.input_wallet)

        lbl_worker = QLabel("Nom du Worker :")
        self.input_worker = QLineEdit("NasMiner01")
        self.input_worker.setStyleSheet("background-color: #1a1a1a; color: white; padding: 5px;")
        form_right.addWidget(lbl_worker)
        form_right.addWidget(self.input_worker)

        form_layout.addLayout(form_left)
        form_layout.addLayout(form_right)
        layout.addLayout(form_layout)

        # Puissance threads
        threads_layout = QHBoxLayout()
        lbl_threads = QLabel("Nombre de threads (puissance) :")
        self.slider_threads = QSlider(Qt.Orientation.Horizontal)
        self.slider_threads.setMinimum(1)
        self.slider_threads.setMaximum(psutil.cpu_count())
        self.slider_threads.setValue(1)
        self.slider_threads.setTickInterval(1)
        self.slider_threads.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_threads.valueChanged.connect(self.update_threads_label)

        self.label_threads_val = QLabel("1")
        self.label_threads_val.setStyleSheet("color:#ff4444; font-weight:bold;")

        threads_layout.addWidget(lbl_threads)
        threads_layout.addWidget(self.slider_threads)
        threads_layout.addWidget(self.label_threads_val)
        layout.addLayout(threads_layout)

        # Multi-minage checkbox
        self.checkbox_multi = QCheckBox("Multi-minage (tous les coins)")
        self.checkbox_multi.setStyleSheet("color:white; font-weight:bold;")
        layout.addWidget(self.checkbox_multi)

        # Bouton démarrer/arrêter
        self.btn_start = QPushButton("🚀 Lancer le minage")
        self.btn_start.setStyleSheet("""
            background-color: #990000; 
            color: white; 
            font-size: 16px; 
            font-weight: bold; 
            padding: 10px;
            border-radius: 5px;
        """)
        self.btn_start.clicked.connect(self.toggle_mining)
        layout.addWidget(self.btn_start)

        # Label parts acceptés & crypto estimée
        self.label_shares = QLabel("✅ Partages acceptés : 0")
        self.label_shares.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.label_shares)

        self.label_estimate = QLabel("💰 Crypto estimée : 0.000000")
        self.label_estimate.setStyleSheet("color: #ffcc00; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.label_estimate)

        # Logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: black; color: #00ff00; font-family: Consolas; font-size: 10pt;")
        layout.addWidget(self.log_text)

        self.tab_mining.setLayout(layout)

    def setup_tab_stats(self):
        layout = QVBoxLayout()

        self.canvas = PlotCanvas(self, width=8, height=4)
        layout.addWidget(self.canvas)

        self.label_power = QLabel("⚡ Estimation consommation électricité: 0.000 kWh")
        self.label_power.setStyleSheet("color: #8888ff; font-family: Consolas; font-size: 12px;")
        layout.addWidget(self.label_power)

        # Crypto mined breakdown
        self.label_mined_breakdown = QLabel("Crypto minée (estimée) :\n" + "\n".join([f"{c}: 0.000000" for c in CRYPTO_LIST.keys()]))
        self.label_mined_breakdown.setStyleSheet("color: #ffcc00; font-family: Consolas; font-size: 12px;")
        layout.addWidget(self.label_mined_breakdown)

        self.tab_stats.setLayout(layout)

    def setup_tab_config(self):
        layout = QVBoxLayout()

        lbl_info = QLabel("Configuration de base (wallets sauvegardés):")
        lbl_info.setStyleSheet("font-weight: bold; color: #ff4444; font-size: 14px;")
        layout.addWidget(lbl_info)

        self.config_text = QTextEdit()
        self.config_text.setPlainText(json.dumps(self.wallets, indent=4))
        self.config_text.setStyleSheet("background-color: #1a1a1a; color: #ff4444; font-family: Consolas; font-size: 11px;")
        layout.addWidget(self.config_text)

        btn_save_config = QPushButton("💾 Sauvegarder la configuration")
        btn_save_config.setStyleSheet("background-color: #990000; color: white; font-weight: bold; padding: 8px;")
        btn_save_config.clicked.connect(self.save_config)
        layout.addWidget(btn_save_config)

        self.tab_config.setLayout(layout)

    def select_coin(self, coin):
        # Uncheck all other coins buttons
        for c, btn in self.coin_buttons.items():
            if c != coin:
                btn.setChecked(False)
        self.selected_coin = coin
        self.input_wallet.setText(self.wallets.get(coin, ""))
        self.log(f"⚡ Coin sélectionné : {coin}")

    def update_threads_label(self):
        self.label_threads_val.setText(str(self.slider_threads.value()))

    def toggle_mining(self):
        if self.mining_threads:
            self.stop_mining()
        else:
            self.start_mining()

    def start_mining(self):
        wallet = self.input_wallet.text().strip()
        worker = self.input_worker.text().strip()
        threads = self.slider_threads.value()
        multi = self.checkbox_multi.isChecked()

        if not wallet or not worker:
            self.log("❌ Wallet ou worker manquant.")
            return

        coins = list(self.wallets.keys()) if multi else [self.selected_coin]

        self.accepted_shares = 0
        self.mined_crypto = {coin: 0.0 for coin in coins}
        self.update_stats_labels()

        self.btn_start.setText("⛏️ Minage en cours...")
        self.btn_start.setEnabled(False)
        self.log(f"[{datetime.now().strftime('%H:%M:%S')}] Démarrage du minage sur : {', '.join(coins)}")

        self.mining_threads = []
        for coin in coins:
            cmd, _ = get_xmrig_cmd(coin, wallet, worker, threads)
            thread = MinerThread(cmd, coin)
            thread.new_log.connect(self.log)
            thread.share_accepted.connect(self.on_share_accepted)
            thread.start()
            self.mining_threads.append(thread)

    def stop_mining(self):
        self.log(f"[{datetime.now().strftime('%H:%M:%S')}] Arrêt du minage...")
        for thread in self.mining_threads:
            thread.stop()
            thread.wait()
        self.mining_threads = []
        self.btn_start.setText("🚀 Lancer le minage")
        self.btn_start.setEnabled(True)

    def on_share_accepted(self, coin):
        self.accepted_shares += 1
        self.mined_crypto[coin] += RATE_ESTIMATE.get(coin, 0.0)
        self.update_stats_labels()

    def update_stats_labels(self):
        self.label_shares.setText(f"✅ Partages acceptés : {self.accepted_shares}")
        total_mined = sum(self.mined_crypto.values())
        self.label_estimate.setText(f"💰 Crypto estimée : {total_mined:.6f}")

        breakdown = "\n".join([f"{c}: {v:.6f}" for c,v in self.mined_crypto.items()])
        self.label_mined_breakdown.setText("Crypto minée (estimée) :\n" + breakdown)

    def update_stats(self):
        ram = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=None)
        power_kwh = (cpu / 100) * 0.065  # approx 65W per hour full CPU
        self.label_power.setText(f"⚡ Estimation consommation électricité: {power_kwh:.3f} kWh")

        now = datetime.now().strftime("%H:%M:%S")
        self.canvas.update_plot(now, cpu, ram)

        QTimer.singleShot(2000, self.update_stats)

    def log(self, msg):
        self.log_text.append(msg)

    def save_config(self):
        try:
            wallets = json.loads(self.config_text.toPlainText())
            save_wallets(wallets)
            self.wallets = wallets
            self.log("💾 Configuration sauvegardée.")
        except Exception as e:
            self.log(f"❌ Erreur sauvegarde configuration : {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NasMinerApp()
    sys.exit(app.exec())
