#!/bin/bash

python MutantSus_calculator.py 2>&1 | tee "../Sus/Mutant/Defects4J/log.txt"
if [ $? -ne 0 ]; then
    echo "Error executing MutantSus_calculator.py"
    exit 1
fi

python MutantSusEx_calculator.py 2>&1 | tee "../Sus/Mutant/Defects4J/Exlog.txt"
if [ $? -ne 0 ]; then
    echo "Error executing MutantSusEx_calculator.py"
    exit 1
fi

python StatementSus_calculator.py 2>&1 | tee "../Sus/Statement/Defects4J/log.txt"
if [ $? -ne 0 ]; then
    echo "Error executing StatementSus_calculator.py"
    exit 1
fi

python StatementRank_statistic.py 2>&1 | tee "../Rank/Statement/Defects4J/log.txt"
if [ $? -ne 0 ]; then
    echo "Error executing StatementRank_statistic.py"
    exit 1
fi

python StatementSusEx_calculator.py 2>&1 | tee "../Sus/Statement/Defects4J/Exlog.txt"
if [ $? -ne 0 ]; then
    echo "Error executing StatementSusEx_calculator.py"
    exit 1
fi

python StatementRank_statistic.py 2>&1 | tee "../Rank/Statement/Defects4J/log.txt"
if [ $? -ne 0 ]; then
    echo "Error executing StatementRank_statistic.py"
    exit 1
fi

python Metric_calcutor.py 2>&1 | tee "../Metric/Statement/Defects4J/log.txt"
if [ $? -ne 0 ]; then
    echo "Error executing Metric_calcutor.py"
    exit 1
fi