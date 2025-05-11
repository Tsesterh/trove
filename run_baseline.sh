#!/usr/bin/env bash

#SBATCH --job-name=baseline_primitive_algebra_5_seed5
#SBATCH --cpus-per-task=4
#SBATCH --mem=60G
#SBATCH --mail-user=tobias.sesterhenn@tu-clausthal.de
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu-vram-48gb


source /home/tsesterh/miniconda3/etc/profile.d/conda.sh
conda activate trove_env

#uvicorn server.gqa:app --port 8002 &

#choices=[
#                            "math/algebra", "math/counting", "math/geometry",
#                            "math/intermediate", "math/number",
#                            "math/prealgebra", "math/precalculus",
#                            "tabmwp", "wtq", "hitab", "gqa"
#                        ],

TASK_NAME="math/algebra"
SEED=5
SUFFIX="primitive"
NUM_RETURN_SEQUENCES=5
MODEL_NAME="codellama/CodeLlama-7b-Instruct-hf"

python baseline.py \
    --seed $SEED \
    --task_name $TASK_NAME \
    --suffix $SUFFIX \
    --num_return_sequences $NUM_RETURN_SEQUENCES \
    --model_name $MODEL_NAME 

