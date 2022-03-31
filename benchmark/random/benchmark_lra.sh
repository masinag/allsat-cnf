DIR=lra_bench
mkdir -p $DIR/data $DIR/results $DIR/plots
python3 generate.py -b 5 -r 5 -d 6 -o $DIR/data -m 20

for dir in $(ls $DIR/data)
do
    for mode in TTA AUTO ACT CND
    do
        python3 evaluate.py $DIR/data/$dir -m $mode -o $DIR/results
    done
done

python3 plot.py $DIR/results -o $DIR/plots