#!/usr/bin/env bash

#SBATCH --job-name=trove_geometry_seed36
#SBATCH --cpus-per-task=2
#SBATCH --mem=80G
#SBATCH --mail-user=tobias.sesterhenn@tu-clausthal.de
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu-vram-48gb

source /home/tsesterh/miniconda3/etc/profile.d/conda.sh
conda activate trove_env

SEED=36
TASK_NAME="math/geometry"
MODEL_NAME="codellama/CodeLlama-7b-Instruct-hf"

python run_trove.py \
    --seed $SEED \
    --task_name $TASK_NAME \
    --model_name $MODEL_NAME
