from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import (
    ModelConfig,
    DPOConfig,
    DPOScriptArguments,
    TrlParser,
    get_peft_config
)
from stepdpo_trainer import StepDPOTrainer
import torch

def dataset_preprocess(example):
    prompt = example["prompt"]
    initial_reason_steps = example["initial_reason_steps"]
    chosen_step = example["chosen_step"]
    rejected_step = example["rejected_step"]
    return {
        "prompt": prompt + initial_reason_steps,
        "chosen": chosen_step,
        "rejected": rejected_step
    }

def main(script_args, training_args, model_args):
    ################
    # Model & Tokenizer
    ################
    torch_dtype = (
        model_args.torch_dtype if model_args.torch_dtype in ["auto", None] else getattr(torch, model_args.torch_dtype)
    )
    model_kwargs = dict(
        revision=model_args.model_revision,
        attn_implementation=model_args.attn_implementation,
        torch_dtype=torch_dtype,
        use_cache=False if training_args.gradient_checkpointing else True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path, trust_remote_code=model_args.trust_remote_code, **model_kwargs
    )
    peft_config = get_peft_config(model_args)
    ref_model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path, trust_remote_code=model_args.trust_remote_code, **model_kwargs
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path, trust_remote_code=model_args.trust_remote_code
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    ################
    # Dataset
    ################
    dataset = load_dataset("json", data_files={"train": script_args.dataset_train_split})
    column_names = list(dataset["train"].features)
    dataset = dataset.map(dataset_preprocess, remove_columns=column_names, desc="Formatting comparisons with prompt template",)
    print("************ SAMPLE ***********")
    print(dataset["train"][0])
    print("*******************************")
    
    ################
    # Training
    ################
    trainer = StepDPOTrainer(
        model=model,
        ref_model=ref_model,
        tokenizer=tokenizer,
        args=training_args,
        beta=training_args.beta,
        train_dataset=dataset["train"],
        peft_config=peft_config,
        force_use_ref_model=True
    )

    trainer.train()

    model.save_pretrained(training_args.output_dir)
    tokenizer.save_pretrained(training_args.output_dir)

def make_parser():
    dataclass_types = (DPOScriptArguments, DPOConfig, ModelConfig)
    parser = TrlParser(dataclass_types)
    return parser

if __name__ == "__main__":
    parser = make_parser()
    script_args, training_args, model_args = parser.parse_args_and_config()
    main(script_args, training_args, model_args)