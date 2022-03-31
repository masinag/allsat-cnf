DIR=bool_bench
mkdir -p $DIR/data $DIR/results $DIR/plots
python3 generate.py -b 10 -r 0 -d 10 -o $DIR/data -m 100

for mode in CND
do
    python3 evaluate.py $DIR/data/* -m $mode -o $DIR/results
done

python3 plot.py $DIR/results -o $DIR/plots