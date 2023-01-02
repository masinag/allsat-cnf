DIR=bool_bench
mkdir -p $DIR/data $DIR/results $DIR/plots
BOOL=$1
DEPTH=$2
python3 generate_bool.py -b $BOOL -d $DEPTH -s 666 -o $DIR/data -m 100

for dir in $(ls -d $DIR/data/*b${BOOL}_d${DEPTH}*)
do
    res_dir=$(sed "s+data+results+g" <<< $dir)
    mkdir -p $res_dir
    for mode in AUTO CND
    do
        python3 evaluate.py $dir -m $mode -o $res_dir
    done
done

python3 plot.py $DIR/results/*b${BOOL}_d${DEPTH}* -o $DIR/plots
