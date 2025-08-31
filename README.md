# SmartCabAlloc_MoveInSync
this if project for interview process of MoveInSync. My topic is Smart Cab Allocation System for Efficient Trip Planning

project documentation link : "i will update link shortly"

## To run this project : 
1. clone repo : `git clone https://github.com/shreekar2005/SmartCabAlloc_MoveInSync.git`
2. cd to repo : `cd SmartCabAlloc_MoveInSync/`
3. activate your virtual python environment : `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `export FLASK_APP=run.py`
6. `flask db init`  # Run this only if the 'migrations' directory doesn't exist
7. `flask db migrate -m "Initial migration"`
8. `flask db upgrade`
9. `python generate_graph.py`
10. `python run.py`
11. `python simulate_cabs.py` # if you want to move cabs in real time
12. goto http://127.0.0.1:5000 and then you will find login directions :) 