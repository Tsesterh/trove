"""Generate Programs with Primitives / Independent Function Induction."""
print("Importing Libraries...")
import os
import torch
import argparse
import transformers
from utils import *
from torch.utils.data import Dataset
from mako.template import Template
from transformers import AutoTokenizer
from tqdm import tqdm
import random

os.environ["TOKENIZERS_PARALLELISM"] = "false"

#set cuda visible devices to 2 and 3#
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"


def main():
    print("Starting the program")

    #set args seed
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    
    # Load data
    print("Loading dataset...")
    examples = load_dataset(args.task_name, args.max_num_examples)
    template_path = os.path.join("prompt", args.task_name, "primitive.md")
    template = Template(filename=template_path)

    if '/' in args.task_name:
        print("Splitting task name for special format")
        args.task_name = args.task_name.split('/')[0]
        
    print("Loading toolbox...")
    library = load_toolbox(os.path.join("toolbox", f"{args.task_name}.py"))
    library_preview = format_toolbox(library)

    print("Initializing tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    print("Preparing dataset...")
    class TempDataset(Dataset):
        def __init__(self, examples: list[dict]):
            self.examples = examples
            self.prompts = []
            self.num_input_tokens = []
            for ex in self.examples:
                prompt_args = PROMPT_ARGS_FUNC[args.task_name](ex)
                prompt_args.update({"toolbox": library_preview})
                prompt = template.render(**prompt_args)
                self.prompts.append(prompt)
                num_tokens = len(tokenizer(prompt)["input_ids"])
                self.num_input_tokens.append(num_tokens)
        
        def __len__(self) -> int:
            return len(self.prompts)
        
        def __getitem__(self, index: int) -> str:
            return self.prompts[index]

    dataset = TempDataset(examples)
    max_output_tokens = max(dataset.num_input_tokens) + args.max_new_tokens
    print(f"Dataset prepared with max output tokens: {max_output_tokens}")

    # Config generation pipeline
    print("Setting up generation pipeline...")
    pipeline = transformers.pipeline(
        "text-generation", model=args.model_name,
        torch_dtype=torch.float16, device_map="auto",
    )
    pipeline.tokenizer.pad_token_id = pipeline.model.config.eos_token_id
    stable_generate_args = {
        "do_sample": True,
        "num_return_sequences": args.num_return_sequences,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "pad_token_id": tokenizer.eos_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "max_length": max_output_tokens,
    }

    # Batched inference
    print("Starting batched inference...")
    model_outputs = []
    for batch_outputs in tqdm(pipeline(
        dataset, batch_size=args.batch_size, **stable_generate_args
    )):
        model_outputs.append(batch_outputs)

    # Execute, evaluate, and log
    print("Executing and logging results...")
    fw_log = open(args.output_log_path, 'w')

    #write all the parser arguments to the log file
    fw_log.write("\n\n\n")
    fw_log.write("Parser Arguments\n")
    fw_log.write(str(args))
    fw_log.write("\n\n\n")

    result_list = []

    for i in range(len(dataset)):
        print(f"Processing example {i+1}...")
        write_prompt(fw_log, dataset.prompts[i], library_preview, i)

        response_list = []
        for r in model_outputs[i]:
            resp = extract_llama_response(
                output_text=r["generated_text"], input_text=dataset.prompts[i]
            )
            resp = parse_model_response(resp)
            response_list.append(resp)

        for j, res in enumerate(response_list):
            code_pieces = []
            for _, func_dict in library.items():
                code_pieces.append(func_dict["function"])
            for func_dict in res["function"]:
                code_pieces.append(func_dict["function"])
            code_pieces.append(unwrap_code(res["solution"]))
            code_pieces = clean_import(code_pieces)

            is_success, exec_output = execute_code_wrapped(
                code_pieces=code_pieces,
                exec_file=args.exec_file,
                timeout=args.exec_timeout,
            )
            ex = dataset.examples[i]
            if "answer" in ex:
                answer = ex["answer"]
            elif "answers" in ex:
                answer = ex["answers"]
            else:
                raise ValueError(f"Invalid example without answers: {ex.keys()}")

            is_correct, model_answer = EVAL_FUNC[args.task_name](
                is_success=is_success, model_output=exec_output,
                answer=answer, return_answers=True,
            )
            exec_dict = {
                "is_success": is_success,
                "is_correct": is_correct,
                "exec_output": exec_output,
                "model_answers": model_answer,
                "answer": answer,
            }

            response_list[j].update(exec_dict)

            write_exec_result(fw_log, exec_dict, index=j)
            write_solution_and_tools(
                fw_log, res, library, index=j,
                update_toolbox=(args.suffix=="instance") and is_success
            )

        best_index = select_best_solution(response_list)

        ## add to tuple of question and response -> Ich will eine Liste haben und dann über kNN immer zur Laufzeit die nächsten Nachbarn finden
        ans_resp_tuple = (dataset.examples[i]["question"], response_list[best_index]["solution"])

        result_list.append(response_list[best_index])
        fw_log.write(f"\n\n**Best Index: {best_index}**\n")

        if (i+1) % args.report_steps == 0:
            print(f"Finished processing {i+1} examples.")

    correct_list = [r["is_correct"] for r in result_list]
    test_acc = sum(correct_list) / len(correct_list)
    fw_log.write(f"\n## Overall Accuracy: Test {test_acc:.2f}\n")
    fw_log.write(f"Toolbox Size: #{len(library)}")
    for name,d in library.items():
        fw_log.write(f"=== {name} ===\n")
        fw_log.write(d["function"])
        fw_log.write("\n\n\n")
    fw_log.close()

    dump_json_file(result_list, args.output_results_path)
    print(f"Overall Accuracy: Test {test_acc:.2f}")
    print(f"Toolbox Size: #{len(library)}")




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_name", type=str, required=True,
                        choices=[
                            "math/algebra", "math/counting", "math/geometry",
                            "math/intermediate", "math/number",
                            "math/prealgebra", "math/precalculus",
                            "tabmwp", "wtq", "hitab", "gqa"
                        ],
                        help="Task name.")

    # experiment settings
    parser.add_argument("--suffix", type=str, required=True,
                        choices=["primitive", "instance"])
    
    # seed
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    
    # example config
    parser.add_argument("--run_index", type=int, default=None)
    parser.add_argument("--max_num_examples", type=int, default=None,
                        help="Maximum number of examples to experiment.")
    parser.add_argument("--report_steps", type=int, default=5,
                        help="Report every N examples.")

    # execution config
    parser.add_argument("--exec_file", type=str, default="tmp_exec.py",
                        help="Temporary execution file.")
    parser.add_argument("--exec_timeout", type=int, default=100,
                        help="Timeout for execution in seconds.")

    # generation config
    parser.add_argument("--model_name", type=str,
                        default="codellama/CodeLlama-7b-Instruct-hf")
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--num_return_sequences", type=int, default=15)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--batch_size", type=int, default=1)

    args = parser.parse_args()
    args = auto_decide_path(args, fields=["log"])

    main()
