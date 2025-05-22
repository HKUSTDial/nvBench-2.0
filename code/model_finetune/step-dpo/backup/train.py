from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import (
    ModelConfig,
    DPOScriptArguments,
    DPOConfig,
    TrlParser
)
from stepdpo_trainer import StepDPOTrainer

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
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_args.model_name_or_path,
        load_in_4bit=model_args.load_in_4bit,
        max_seq_length=training_args.max_length,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    peft_model = FastLanguageModel.get_peft_model(
        model=model,
        r=model_args.lora_r,
        lora_alpha=model_args.lora_alpha,
        lora_dropout=model_args.lora_dropout,
        use_gradient_checkpointing=training_args.gradient_checkpointing,
        max_seq_length=training_args.max_length
    )
    ################
    # Dataset
    ################
    dataset = load_dataset("json", data_files={"train": script_args.dataset_train_split})
    dataset = dataset.map(dataset_preprocess)
    print("************ SAMPLE ***********")
    print(dataset["train"][0])
    print("*******************************")
    
    ################
    # Training
    ################
    trainer = StepDPOTrainer(
        model=peft_model,
        ref_model=model,
        tokenizer=tokenizer,
        args=training_args,
        beta=training_args.beta,
        train_dataset=dataset["train"],
        max_length=training_args.max_length,
        max_prompt_length=training_args.max_prompt_length,
        loss_type=training_args.loss_type
    )

    trainer.train()

    peft_model.save_pretrained(training_args.output_dir)
    tokenizer.save_pretrained(training_args.output_dir)

def make_parser():
    dataclass_types = (DPOScriptArguments, DPOConfig, ModelConfig)
    parser = TrlParser(dataclass_types)
    return parser

if __name__ == "__main__":
    parser = make_parser()
    script_args, training_args, model_args = parser.parse_args_and_config()
    main(script_args, training_args, model_args)