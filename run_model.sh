echo "Run model with keep prob 0.5"
python3 main.py --DROPOUT=0.5 --EPOCHS=1

echo "Run model with keep prob 0.75"
python3 main.py --DROPOUT=0.75 --EPOCHS=1

echo "Run model with keep prob 1.0"
python3 main.py --DROPOUT=1.0 --EPOCHS=1