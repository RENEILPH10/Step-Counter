import sys
import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QGraphicsDropShadowEffect
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
        self.setMinimumSize(760, 520)
        QApplication.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("background-color: white; color: black;")

        # State (silmulation)
        self.gps = GPSSimulator()
        self.prev_coord = None
        self.prev_time = None
        self.total_distance_m = 0.0
        self.current_speed_m_s = 0.0
        self.steps_est = 0

        # DB
        self.db = Database(DB_FILE)
        self.db.init_db()

        # Build UI
        self.my_ui()

        # Timer (real-time)
        self.timer = QTimer(self)
        self.timer.setInterval(POLL_INTERVAL_MS)
        self.timer.timeout.connect(self.poll_and_update)
        self.timer.start()
        # initial update
        QTimer.singleShot(100, self.poll_and_update)

    def my_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(14,14,14,14)
        main_layout.setSpacing(12)

        title = QLabel("COUNT YOUR STEP")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: black;")
        main_layout.addWidget(title)

        # dashboard for 
        dash1 = QFrame()
        dash1.setStyleSheet("background-color: black; border-radius: 12px;")
        shadow = QGraphicsDropShadowEffect(self); 
        shadow.setBlurRadius(16); 
        shadow.setOffset(0,6); 
        shadow.setColor(QColor(0,0,0,120))
        dash1.setGraphicsEffect(shadow)
        dash1_layout = QHBoxLayout(); 
        dash1_layout.setContentsMargins(20,20,20,20); 
        dash1_layout.setSpacing(30)

        self.lbl_speed_val = QLabel("0.0"); 
        self.lbl_speed_val.setStyleSheet("color: white;"); 
        self.lbl_speed_val.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.lbl_speed_label = QLabel("km/h"); 
        self.lbl_speed_label.setStyleSheet("color: #dddddd;")
        spd_box = QVBoxLayout(); 
        spd_box.addWidget(self.lbl_speed_val, alignment=Qt.AlignCenter); 
        spd_box.addWidget(self.lbl_speed_label, alignment=Qt.AlignCenter)

        self.lbl_steps_val = QLabel("0"); 
        self.lbl_steps_val.setStyleSheet("color: white;"); 
        self.lbl_steps_val.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.lbl_steps_label = QLabel("STEPS"); 
        self.lbl_steps_label.setStyleSheet("color: #dddddd;")
        step_box = QVBoxLayout(); 
        step_box.addWidget(self.lbl_steps_val, alignment=Qt.AlignCenter); 
        step_box.addWidget(self.lbl_steps_label, alignment=Qt.AlignCenter)

        self.lbl_km_val = QLabel("0.00"); 
        self.lbl_km_val.setStyleSheet("color: white;"); 
        self.lbl_km_val.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.lbl_km_label = QLabel("KM"); 
        self.lbl_km_label.setStyleSheet("color: #dddddd;")
        km_box = QVBoxLayout(); km_box.addWidget(self.lbl_km_val, alignment=Qt.AlignCenter); 
        km_box.addWidget(self.lbl_km_label, alignment=Qt.AlignCenter)

        dash1_layout.addLayout(spd_box); 
        dash1_layout.addLayout(step_box); 
        dash1_layout.addLayout(km_box)
        dash1.setLayout(dash1_layout)
        main_layout.addWidget(dash1, stretch=1)

        # Controls
        controls = QHBoxLayout(); controls.setSpacing(12)
        self.btn_stop = QPushButton("Stop"); 
        self.btn_start = QPushButton("Start"); 
        self.btn_reset = QPushButton("Reset")
        self.btn_save = QPushButton("Save Record"); 
        self.btn_refresh = QPushButton("Refresh History")
        
        for b in (self.btn_stop, self.btn_start, self.btn_reset, self.btn_save, self.btn_refresh):
            b.setFixedHeight(36)
            b.setStyleSheet("""
                QPushButton { background-color: black; color: white; border-radius: 8px; padding:6px 12px; font-weight:600; }
                QPushButton:hover { background-color:#222; }
                QPushButton:pressed { background-color:#000000; }
            """)

        controls.addWidget(self.btn_stop); 
        controls.addWidget(self.btn_start); 
        controls.addWidget(self.btn_reset); 
        controls.addWidget(self.btn_save); 
        controls.addWidget(self.btn_refresh)
        main_layout.addLayout(controls)

        # Records Dashboard
        rec_dash = QFrame(); 
        rec_dash.setStyleSheet("background-color: black; border-radius:12px;")
        rec_layout = QVBoxLayout(); 
        rec_layout.setContentsMargins(12,12,12,12)
        rec_title = QLabel("RECORDS"); 
        rec_title.setFont(QFont("Segoe UI", 12, QFont.Bold)); 
        rec_title.setStyleSheet("color:white;")
        rec_layout.addWidget(rec_title, alignment=Qt.AlignLeft)
        self.table = QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["Datetime","Distance (km)","Speed (km/h)","Steps"])

        header = self.table.horizontalHeader(); 
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("QTableWidget { background: white; } QHeaderView::section{ background: #f0f0f0 }")
        rec_layout.addWidget(self.table)
        rec_dash.setLayout(rec_layout)
        main_layout.addWidget(rec_dash, stretch=1)

        self.setLayout(main_layout)

        # Connect buttons
        self.btn_start.clicked.connect(self.on_start); 
        self.btn_stop.clicked.connect(self.on_stop); 
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_save.clicked.connect(self.on_save); 
        self.btn_refresh.clicked.connect(self.records)

    def poll_and_update(self):
        coord = self.gps.next_coord()
        now = time.time()

        if self.prev_coord is None:
            self.prev_coord = coord
            self.prev_time = now
            self.current_speed_m_s = 0.0
        else:
            meters = haversine(self.prev_coord, coord)
            elapsed = now - self.prev_time if self.prev_time else 1.0
            speed_m_s = meters / elapsed if elapsed>0 else 0.0
            self.total_distance_m += meters
            self.current_speed_m_s = speed_m_s
            self.prev_coord = coord
            self.prev_time = now
            self.steps_est = int(self.total_distance_m / STEP_METERS)
        self.update_ui()

    def update_ui(self):
        km = self.total_distance_m / 1000.0
        self.lbl_km_val.setText(f"{km:.2f}")
        self.lbl_steps_val.setText(str(int(self.steps_est)))
        speed_kmh = self.current_speed_m_s * 3.6
        self.lbl_speed_val.setText(f"{speed_kmh:.1f}")

    def on_start(self):
        if not self.timer.isActive():
            self.prev_coord = None; 
            self.prev_time = None; 
            self.total_distance_m = 0.0; self.current_speed_m_s = 0.0; 
            self.steps_est = 0
            self.timer.start()

    def on_stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def on_reset(self):
        res = QMessageBox.question(self, "Confirm Reset", "Reset live counters?")
        if res != QMessageBox.Yes: return
        self.prev_coord = None; 
        self.prev_time = None; 
        self.total_distance_m = 0.0; 
        self.current_speed_m_s = 0.0; 
        self.steps_est = 0
        self.update_ui()

    def on_save(self):
        dist_km = self.total_distance_m / 1000.0
        speed_kmh = self.current_speed_m_s * 3.6
        steps = int(self.steps_est)
        self.db.insert_record(datetime.now().isoformat(sep=' ', timespec='seconds'), dist_km, speed_kmh, steps)
        QMessageBox.information(self, "Saved", "Record saved to database.")
        self.records()

    def records(self):
        rows = self.db.fetch_records()
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r,0,QTableWidgetItem(row[0])); 
            self.table.setItem(r,1,QTableWidgetItem(f"{row[1]:.3f}")); 
            self.table.setItem(r,2,QTableWidgetItem(f"{row[2]:.2f}")); 
            self.table.setItem(r,3,QTableWidgetItem(str(row[3])))

    def closeEvent(self, event):
        try: self.db.close()
        finally: event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StepSpeedApp()
    window.show()
    window.records()
    sys.exit(app.exec_())
