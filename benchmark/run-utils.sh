# add option for with_repetition flag
run() {
  DIR=$1
  SAT=$2
  RES_DIR=$3
  REP_FLAG=$4
  QUERY=${5:-*}
  for dir in $(ls -d $DIR/data/$QUERY); do
    res_dir=$(sed "s+data+${RES_DIR}+g" <<<$dir)
    mkdir -p "$res_dir"
    echo $dir
    for mode in LAB NNF_MUTEX_POL LABELNEG_POL; do
      python3 ../evaluate.py "$dir" -m $mode -o "$res_dir" $SAT $REP_FLAG
    done
  done
}

get-allsat() {
  run $1 "" "results" $2 $3
}

check-sat() {
  run $1 "--sat" "results-sat" "" $2
}
