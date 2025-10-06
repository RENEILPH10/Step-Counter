# Step Counter

Author: Lhoreneil I. Jose

## Overview
This is a standalone Step Counter and Speedometer desktop application built with PyQt5.
It simulates small GPS movements (walking pace) and uses the Haversine formula to compute distance.
The application shows real-time Speed, Distance (km), and Steps (estimated) and allows saving sessions to an SQLite database.

## Files
- `main.py` : Main GUI and application logic.
- `gps_tracker.py` : Haversine function and GPSSimulator (small random moves).
- `database.py` : SQLite helper class.
- `requirements.txt` : dependencies.
- `records.db` : created when running the app and saving records.

## Run
1. Install requirements:
```
pip install -r requirements.txt
```
2. Run:
```
python main.py
```
The app auto-starts tracking with simulated GPS movement. Use the buttons to Stop/Start/Reset and Save records.
