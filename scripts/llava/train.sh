# NOTE: you can replace with your dataset path where there is a train-llava.json
DATA_DIR=$(python -c 'from legent import get_latest_folder; print(get_latest_folder(".legent/dataset"))')

# create output directory
_DATE=$(python -c 'from legent import time_string; print(time_string())')
MODEL_BASE=.legent/models/base/llava-v1.5-7b
VISION_TOWER=.legent/models/base/clip-vit-large-patch14-336
OUTPUT_DIR=.legent/models/llava-v1.5-7b/$_DATE
python -c "import os; os.makedirs('$OUTPUT_DIR')"
cp scripts/llava/train.sh $OUTPUT_DIR
echo "Training... (dataset: $DATA_DIR)"
echo "See log in $OUTPUT_DIR/log.txt"

GPU_MODEL=$(nvidia-smi -L | grep "4090")
if [ ! -z "$GPU_MODEL" ]; then
    export NCCL_P2P_DISABLE=1
    echo "Detected RTX 4090: Setting NCCL_P2P_DISABLE=1"
else
    export NCCL_P2P_DISABLE=0
fi

# train and save the model
# See legent/model/llava/model/llava_arch.py
# If mm_vision_tower exists in config.json, vision_tower will not be used. Here vision_tower is not used.
deepspeed --include=localhost:0,1 scripts/llava/train.py \
    --lora_enable True --lora_r 128 --lora_alpha 256 --mm_projector_lr 2e-5 \
    --deepspeed scripts/llava/zero3.json \
    --model_name_or_path $MODEL_BASE \
    --version v1 \
    --data_path $DATA_DIR/train-llava.json \
    --image_folder $DATA_DIR \
    --vision_tower $VISION_TOWER \
    --mm_projector_type mlp2x_gelu \
    --mm_vision_select_layer -2 \
    --mm_use_im_start_end False \
    --mm_use_im_patch_token False \
    --image_aspect_ratio pad \
    --group_by_modality_length True \
    --bf16 True \
    --output_dir $OUTPUT_DIR \
    --num_train_epochs 1 \
    --per_device_train_batch_size 4 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 1 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 50000 \
    --save_total_limit 1 \
    --learning_rate 2e-4 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --lr_scheduler_type "cosine" \
    --logging_steps 1 \
    --tf32 True \
    --model_max_length 2048 \
    --gradient_checkpointing True \
    --dataloader_num_workers 4 \
    --lazy_preprocess True \
    --report_to none \
    >> "$OUTPUT_DIR/log.txt"

echo "merge lora weights..."

# merge lora
python -c "import os; os.makedirs(\"$OUTPUT_DIR/llava-merged\")"
python scripts/llava/merge_lora_weights.py \
    --model-path $OUTPUT_DIR/llava-lora \
    --model-base $MODEL_BASE \
    --save-model-path $OUTPUT_DIR/llava-merged \
    >> "$OUTPUT_DIR/log.txt"

echo "Training completed. Model save path: $OUTPUT_DIR/llava-merged"
echo "Deploy the model by running:"
echo "    MODEL_PATH=$OUTPUT_DIR/llava-merged python scripts/llava/serve.py"
