import sys
import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QGraphicsDropShadowEffect, QGraphicsBlurEffect
)
from gps_tracker import GPSSimulator, haversine
from database import Database
from datetime import datetime

DB_FILE = "records.db"
STEP_METERS = 0.8
POLL_INTERVAL_MS = 1000


class StepSpeedApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Step Counter")
        self.setFixedSize(540, 680  )
        QApplication.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #7b2ff7, stop:1 #fdbb2d ); color: black;")

        # State (simulation)
        self.gps = GPSSimulator()
        self.prev_coord = None
        self.prev_time = None
        self.total_distance_m = 0.0
        self.steps_est = 0
        self.start_time = None
        self.elapsed_time = 0.0

        # Database
        self.db = Database(DB_FILE)
        self.db.init_db()

        # My UI
        self.my_ui()

        # Timer (realtime updates)
        self.timer = QTimer(self)
        self.timer.setInterval(POLL_INTERVAL_MS)
        self.timer.timeout.connect(self.poll_and_update)
        self.timer.start()
        QTimer.singleShot(100, self.poll_and_update)

    def my_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(36)

        title = QLabel("COUNT YOUR STEP")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 120))
        title.setGraphicsEffect(shadow)
        title.setFont(QFont("Arsenica ", 30, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
                    color: white;
                    background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 100),
                    stop:1 rgba(255, 200, 200, 80)
                    );
                    border-radius: 20px;
                """)
        main_layout.addWidget(title)

        # Dashboard 1 (Timer, Steps, KM)
        dash1 = QFrame()
        dash1.setStyleSheet("""
                    background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 100),
                    stop:1 rgba(255, 200, 200, 80)
                    );
                    border-radius: 20px;
                """)
        blur = QGraphicsBlurEffect(self)
        blur.setBlurRadius(20)
        dash1.setGraphicsEffect(blur)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 120))
        dash1.setGraphicsEffect(shadow)


        dash1_layout = QHBoxLayout()
        dash1_layout.setContentsMargins(20, 20, 20, 20)
        dash1_layout.setSpacing(30)

        # Timer
        self.lbl_timer = QLabel("00:00")
        self.lbl_timer.setStyleSheet("color: white;background-color: none;")
        self.lbl_timer.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.lbl_timer_label = QLabel("TIMER")
        self.lbl_timer_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.lbl_timer_label.setStyleSheet("color: #dddddd; background-color: none;")
        timer_box = QVBoxLayout()
        timer_box.addWidget(self.lbl_timer, alignment=Qt.AlignCenter)
        timer_box.addWidget(self.lbl_timer_label, alignment=Qt.AlignCenter)

        # Steps
        self.lbl_steps_val = QLabel("0")
        self.lbl_steps_val.setStyleSheet("color: white; background-color: none;")
        self.lbl_steps_val.setFont(QFont("Segoe UI", 36, QFont.Bold))
        self.lbl_steps_label = QLabel("STEPS")
        self.lbl_steps_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_steps_label.setStyleSheet("color: #dddddd;background-color: none;")
        step_box = QVBoxLayout()
        step_box.addWidget(self.lbl_steps_val, alignment=Qt.AlignCenter)
        step_box.addWidget(self.lbl_steps_label, alignment=Qt.AlignCenter)

        # KM
        self.lbl_km_val = QLabel("0.00")
        self.lbl_km_val.setStyleSheet("color: white;background-color: none;")
        self.lbl_km_val.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.lbl_km_label = QLabel("KM")
        self.lbl_km_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.lbl_km_label.setStyleSheet("color: #dddddd;background-color: none;")
        km_box = QVBoxLayout()
        km_box.addWidget(self.lbl_km_val, alignment=Qt.AlignCenter)
        km_box.addWidget(self.lbl_km_label, alignment=Qt.AlignCenter)

        dash1_layout.addLayout(timer_box)
        dash1_layout.addLayout(step_box)
        dash1_layout.addLayout(km_box)
        dash1.setLayout(dash1_layout)
        main_layout.addWidget(dash1, stretch=1)

        # Buttons
        controls = QHBoxLayout()
        controls.setSpacing(12)
        self.btn_stop = QPushButton("Stop")
        self.btn_reset = QPushButton("Reset")
        self.btn_start = QPushButton("Start")
        self.btn_save = QPushButton("Save")
        self.btn_refresh = QPushButton("Refresh")

        for b in (self.btn_stop, self.btn_reset, self.btn_start, self.btn_save, self.btn_refresh):
            b.setFixedHeight(46)
            b.setStyleSheet("""
                QPushButton {
                    background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7b2ff7, stop:1 #fdbb2d
                    );
                    color: white;
                    border-radius: 12px;
                    padding: 8px 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #330000;
                    color: #ff4444;
                    border: 2px solid #ff4444;
                    box-shadow: 0 0 10px rgba(255,68,68,0.5),
                                0 0 20px rgba(255,68,68,0.3),
                                0 0 30px rgba(255,68,68,0.2);
                }
                QPushButton:pressed {
                    background-color: #5a1ea8;
                    filter: brightness(80%);
                    color: white;
                }
            """)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(50)
            shadow.setOffset(0, 6)
            shadow.setColor(QColor(0, 0, 0, 120))
            b.setGraphicsEffect(shadow)


        controls.addWidget(self.btn_stop)
        controls.addWidget(self.btn_reset)
        controls.addWidget(self.btn_start)
        controls.addWidget(self.btn_save)
        controls.addWidget(self.btn_refresh)
        main_layout.addLayout(controls)

        # Dashboard 2 (Records)
        rec_dash = QFrame()
        rec_dash.setStyleSheet("""
                    background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 100),
                    stop:1 rgba(255, 200, 200, 80)
                    );
                    border-radius: 20px;
                """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 120))
        rec_dash.setGraphicsEffect(shadow)

        rec_layout = QVBoxLayout()
        rec_layout.setContentsMargins(12, 12, 12, 12)

        rec_title = QLabel("RECORDS")
        rec_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        rec_title.setStyleSheet("color:white; background-color: none;")
        rec_layout.addWidget(rec_title, alignment=Qt.AlignLeft)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Datetime", "Distance (km)", "Steps"])
        self.table.setStyleSheet("border-radius:12px;")
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: transparent border-radius: 16px;")

        rec_layout.addWidget(self.table)
        rec_dash.setLayout(rec_layout)
        main_layout.addWidget(rec_dash, stretch=1)

        self.setLayout(main_layout)

        # Connect buttons
        self.btn_start.clicked.connect(self.on_start)
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_refresh.clicked.connect(self.records)



    #My Classes
    def poll_and_update(self):
        coord = self.gps.next_coord()
        now = time.time()

        if self.prev_coord is None:
            self.prev_coord = coord
            self.prev_time = now
            self.start_time = now
            self.elapsed_time = 0.0
            self.total_distance_m = 0.0
            self.steps_est = 0
        else:
            meters = haversine(self.prev_coord, coord)
            self.total_distance_m += meters
            self.steps_est = int(self.total_distance_m / STEP_METERS)
            self.elapsed_time = now - self.start_time
            self.prev_coord = coord
            self.prev_time = now

        self.update_ui()

    def update_ui(self):
        rem = divmod(int(self.elapsed_time), 3600)
        minutes, seconds = divmod(rem[1], 60)
        time_str = f"{minutes:02}:{seconds:02}"

        km = self.total_distance_m / 1000.0
        self.lbl_km_val.setText(f"{km:.2f}")
        self.lbl_steps_val.setText(str(int(self.steps_est)))
        self.lbl_timer.setText(time_str)

    def on_start(self):
        if not self.timer.isActive():
            self.prev_coord = None
            self.prev_time = None
            self.total_distance_m = 0.0
            self.steps_est = 0
            self.start_time = time.time()
            self.timer.start()

    def on_stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def on_reset(self):
        res = QMessageBox.question(self, "Confirm Reset", "Reset counters?")
        if res != QMessageBox.Yes:
            return
        self.prev_coord = None
        self.prev_time = None
        self.total_distance_m = 0.0
        self.steps_est = 0
        self.start_time = time.time()
        self.elapsed_time = 0.0
        self.update_ui()

    def on_save(self):
        dist_km = self.total_distance_m / 1000.0
        steps = int(self.steps_est)
        self.db.insert_record(datetime.now().isoformat(sep=' ', timespec='seconds'), dist_km, 0.0, steps)
        QMessageBox.information(self, "Saved", "Record saved to database.")
        self.records()

    def records(self):
        rows = self.db.fetch_records()
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row[0]))
            self.table.setItem(r, 1, QTableWidgetItem(f"{row[1]:.3f}"))
            self.table.setItem(r, 2, QTableWidgetItem(str(row[3])))

    def closeEvent(self, event):
        try:
            self.db.close()
        finally:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StepSpeedApp()
    window.show()
    window.records()
    sys.exit(app.exec_())
