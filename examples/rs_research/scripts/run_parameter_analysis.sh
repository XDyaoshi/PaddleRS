#!/bin/bash

set -e 

CONFIG_DIR='configs/levircd/custom_model'
LOG_DIR='exp/logs/parameter_analysis'

mkdir -p "${LOG_DIR}"

for config_file in $(ls ${CONFIG_DIR}); do
    printf '=%.0s' {1..100} && echo
    echo -e "\033[33m ${config_file} \033[0m"
    printf '=%.0s' {1..100} && echo
    python run_task.py train cd --config "${CONFIG_DIR}/${config_file}" 2>&1 | tee "${LOG_DIR}/${config_file%.*}"
    echo
done
