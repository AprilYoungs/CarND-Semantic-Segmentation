echo "Run model with keep prob 0.5"
python3 main.py --DROPOUT=0.5

echo "Run model with keep prob 0.75"
python3 main.py --DROPOUT=0.75

echo "Run model with keep prob 1.0"
python3 main.py --DROPOUT=1.0