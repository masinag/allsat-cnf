DIR=bool_bench
mkdir -p $DIR/data $DIR/results $DIR/plots
python3 generate_bool.py -b 20 -d 15 -o $DIR/data -m 100

for dir in $(ls $DIR/data)
do
    for mode in TTA AUTO ACT CND
    do
        python3 evaluate.py $DIR/data/$dir -m $mode -o $DIR/results
    done
done

python3 plot.py $DIR/results -o $DIR/plots