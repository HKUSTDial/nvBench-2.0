from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import (
    ModelConfig,
    ScriptArguments,
    SFTConfig,
    TrlParser
)
from sft_template import SFT_PROMPT_STEP_TEMPLATE, SFT_PROMPT_TEMPLATE, STEP_BY_STEP_OUTPUT_TEMPLATE
import json
from tqdm import tqdm
import os

WITH_THINKING = os.getenv("SFT_WITH_THINKING", False)

PROMPT_TEMPLATE = SFT_PROMPT_STEP_TEMPLATE if WITH_THINKING else SFT_PROMPT_TEMPLATE

def dataset_preprocess(examples, tokenizer):
    nl_query_list = examples["nl_query"]
    table_schema_list = examples["table_schema"]
    gold_answer_list = examples["gold_answer"]
    texts = []
    EOS_TOKEN = tokenizer.eos_token
    for nl_query, table_schema, gold_answer in zip(nl_query_list, table_schema_list, gold_answer_list):
        table_schema = json.loads(table_schema)
        text = PROMPT_TEMPLATE.format(
            table_columns=table_schema["table_columns"],
            column_examples="\n".join([f"{k}: {v}" for k, v in table_schema["column_examples"].items()]),
            unique_value_counts="\n".join([f"{k}: {v}" for k, v in table_schema["unique_value_counts"].items()]),
            nl_query=nl_query,
            output="" # leave the output for model generation
        ) # do not add EOS_TOKEN for model input
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
        
    FastLanguageModel.for_inference(model)

    ################
    # Dataset
    ################
    dataset = load_dataset("json", data_files={"eval": script_args.dataset_test_split})
    dataset = dataset.map(lambda x: dataset_preprocess(x, tokenizer), batched=True)
    print("************ SAMPLE ***********")
    print(dataset["eval"][0]["text"])
    print("*******************************")
    
    predictions = []
    
    for text in tqdm(dataset["eval"]["text"]):
        inputs = tokenizer(text, return_tensors="pt")
        input_ids = inputs["input_ids"].to(model.device)
        attention_mask = inputs["attention_mask"].to(model.device)
        outputs = model.generate(input_ids=input_ids, attention_mask=attention_mask, max_new_tokens=2048)
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        prediction = prediction.split("# Output:")[-1].strip()
        predictions.append(json.dumps({"text": text, "prediction": prediction}))
        print("************ TEXT ***********")
        print(text)
        print("************ PREDICTION ***********")
        print(prediction)
        print("*******************************")
    
    with open(training_args.output_dir + "/predictions.jsonl", "w") as f:
        for prediction in predictions:
            f.write(prediction + "\n")

def make_parser():
    dataclass_types = (ScriptArguments, SFTConfig, ModelConfig)
    parser = TrlParser(dataclass_types)
    return parser

if __name__ == "__main__":
    parser = make_parser()
    script_args, training_args, model_args = parser.parse_args_and_config()
    main(script_args, training_args, model_args)