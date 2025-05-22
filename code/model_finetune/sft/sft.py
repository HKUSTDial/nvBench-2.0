from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import (
    ModelConfig,
    ScriptArguments,
    SFTConfig,
    SFTTrainer,
    TrlParser
)
from sft_template import SFT_PROMPT_STEP_TEMPLATE, SFT_PROMPT_TEMPLATE, STEP_BY_STEP_OUTPUT_TEMPLATE
import json

import os

WITH_THINKING = os.getenv("SFT_WITH_THINKING", False)

def dataset_preprocess(examples, tokenizer):
    nl_query_list = examples["nl_query"]
    table_schema_list = examples["table_schema"]
    steps_list = examples["steps"]
    gold_answer_list = examples["gold_answer"]
    texts = []
    EOS_TOKEN = tokenizer.eos_token
    for nl_query, table_schema, steps, gold_answer in zip(nl_query_list, table_schema_list, steps_list, gold_answer_list):
        assert isinstance(table_schema, str) and isinstance(gold_answer, str)
        table_schema = json.loads(table_schema)
        if not WITH_THINKING:
            text = SFT_PROMPT_TEMPLATE.format(
                table_columns=table_schema["table_columns"],
                column_examples="\n".join([f"{k}: {v}" for k, v in table_schema["column_examples"].items()]),
                unique_value_counts="\n".join([f"{k}: {v}" for k, v in table_schema["unique_value_counts"].items()]),
                nl_query=nl_query,
                output=gold_answer
            ) + EOS_TOKEN
        else:
            steps = json.loads(steps)
            output = STEP_BY_STEP_OUTPUT_TEMPLATE.format(
                step_1_thinking=steps["step_1"]["reasoning"].strip(),
                step_1_answer=json.dumps(steps["step_1"]["answer"]),
                step_2_thinking=steps["step_2"]["reasoning"].strip(),
                step_2_answer=json.dumps(steps["step_2"]["answer"]),
                step_3_thinking=steps["step_3"]["reasoning"].strip(),
                step_3_answer=json.dumps(steps["step_3"]["answer"]),
                step_4_thinking=steps["step_4"]["reasoning"].strip(),
                step_4_answer=json.dumps(steps["step_4"]["answer"]),
                step_5_thinking=steps["step_5"]["reasoning"].strip(),
                step_5_answer=json.dumps(steps["step_5"]["answer"]),
                step_6_thinking=steps["step_6"]["reasoning"].strip(),
                step_6_answer=json.dumps(steps["step_6"]["answer"]),
            )
            text = SFT_PROMPT_STEP_TEMPLATE.format(
                table_columns=table_schema["table_columns"],
                column_examples="\n".join([f"{k}: {v}" for k, v in table_schema["column_examples"].items()]),
                unique_value_counts="\n".join([f"{k}: {v}" for k, v in table_schema["unique_value_counts"].items()]),
                nl_query=nl_query,
                output=output
            ) + EOS_TOKEN
        texts.append(text)
    return {"text": texts}

def main(script_args, training_args, model_args):
    ################
    # Model & Tokenizer
    ################
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_args.model_name_or_path,
        load_in_4bit=model_args.load_in_4bit,
        max_seq_length=training_args.max_seq_length,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = FastLanguageModel.get_peft_model(
        model=model,
        r=model_args.lora_r,
        lora_alpha=model_args.lora_alpha,
        lora_dropout=model_args.lora_dropout,
        use_gradient_checkpointing=training_args.gradient_checkpointing,
        max_seq_length=training_args.max_seq_length,
        use_rslora=model_args.use_rslora
    )
    ################
    # Dataset
    ################
    dataset = load_dataset("json", data_files={"train": script_args.dataset_train_split, "eval": script_args.dataset_test_split})
    dataset = dataset.map(lambda x: dataset_preprocess(x, tokenizer), batched=True)
    print("************ SAMPLE ***********")
    print(dataset["train"][0])
    print("*******************************")
    
    ################
    # Training
    ################
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"] if training_args.eval_strategy != "no" else None,
        dataset_text_field="text",
        max_seq_length=training_args.max_seq_length
    )

    trainer.train()

    model.save_pretrained(training_args.output_dir)
    tokenizer.save_pretrained(training_args.output_dir)

def make_parser():
    dataclass_types = (ScriptArguments, SFTConfig, ModelConfig)
    parser = TrlParser(dataclass_types)
    return parser

if __name__ == "__main__":
    parser = make_parser()
    script_args, training_args, model_args = parser.parse_args_and_config()
    main(script_args, training_args, model_args)