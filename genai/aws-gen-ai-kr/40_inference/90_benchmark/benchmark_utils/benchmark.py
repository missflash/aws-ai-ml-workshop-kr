# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""General helper utilities the workshop notebooks"""
# Python Built-Ins:
from io import StringIO
import sys
import textwrap


def print_ww(*args, width: int = 100, **kwargs):
    """Like print(), but wraps output to `width` characters (default 100)"""
    buffer = StringIO()
    try:
        _stdout = sys.stdout
        sys.stdout = buffer
        print(*args, **kwargs)
        output = buffer.getvalue()
    finally:
        sys.stdout = _stdout
    for line in output.splitlines():
        print("\n".join(textwrap.wrap(line, width=width)))

import json

def pretty_print_json(data, sort_keys=False):
    print(json.dumps(data, indent=4, sort_keys=sort_keys))

import boto3

def invoke_endpoint_sagemaker(endpoint_name, pay_load):

    # Set up the SageMaker runtime client
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    # Set the endpoint name
    endpoint_name = endpoint_name


    # Invoke the endpoint
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=json.dumps(pay_load)
    )

    # Get the response from the endpoint
    result = response['Body'].read().decode('utf-8')

    return result

import numpy as np
import concurrent.futures
import time

class Benchmark:
    """benchmark LLM"""

    def __init__(self, endpoint_name):
        self.endpoint_name = endpoint_name
        self.latency_list = list()
        self.completion_token_list = list()

    def run_benchmark(self, num_inferences, num_threads, pay_load, tokenizer, verbose=False):
        '''
        main function to run benchmark
        '''
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_inferences):
                futures.append(executor.submit(self._inference_with_latency_calculation, pay_load))
            for future in concurrent.futures.as_completed(futures):
                get_result = future.result()
                metrics = self._set_metrics(pay_load=pay_load,
                                    response=get_result, 
                                    tokenizer = tokenizer)
                if verbose:                                    
                    print("metrics: ", metrics)
                    print("completion_token_count: ", metrics["completion_token_count"])

                self.completion_token_list.append(metrics["completion_token_count"])
                
        end = time.time()
        total_time = end - start
        total_completion_token_count = sum(self.completion_token_list)
        print(f"## total execution time: {round(total_time,3)} second")
        print("total_completion_token_count: ", total_completion_token_count)


        throughput = (round(total_completion_token_count / total_time, 3))
        print(f"Throughput was {throughput} tokens per second.")
        print(f"Latency p50 was {round(np.percentile(self.latency_list, 50),3)} sec")
        print(f"Latency p95 was {round(np.percentile(self.latency_list, 95),3)} sec")
        print(f"Latency p99 was {round(np.percentile(self.latency_list, 99),3)} sec")

    def _inference_with_latency_calculation(self, pay_load):
        '''
        call invoke inference function
        '''
        start = time.time()
        result = invoke_endpoint_sagemaker(endpoint_name = self.endpoint_name, 
                            pay_load = pay_load)    
        
        end = time.time()
        self.latency_list.append((end-start) )

        return result

    def _set_metrics(self, pay_load,response, tokenizer):
        '''
        set metrics of prompt_token_count, completion_token_count
        '''
        prompt = pay_load["inputs"]
        prompt_token_count, prompt_tokens_text = self._count_tokens(text=prompt, tokenizer = tokenizer)

        completion = json.loads(response)["generated_text"]
        completion_token_count, completion_tokens_text = self._count_tokens(text=completion, tokenizer = tokenizer)

        return dict(prompt_token_count = prompt_token_count,
                    completion_token_count = completion_token_count,
                    )    

    def _count_tokens(self, text, tokenizer):
        '''
        count tokens
        '''
        # 텍스트를 토크나이즈하고 토큰 수를 반환
        tokens = tokenizer.encode(text)
        tokens_text = tokenizer.convert_ids_to_tokens(tokens)
        # print(tokens_text)
        return len(tokens), tokens_text





# class CustomTokenizer:    
#     """A custom tokenizer class"""
#     TOKENS: int = 1000
#     WORDS: int = 750

#     def __init__(self, local_dir):
#         print(f"CustomTokenizer, based on HF transformers")
#         # Load the tokenizer from the local directory
#         dir_not_empty = any(Path(local_dir).iterdir())
#         if dir_not_empty is True:
#             logger.info("loading the provided tokenizer")
#             self.tokenizer = AutoTokenizer.from_pretrained(local_dir)
#         else:
#             logger.error(f"no tokenizer provided, the {local_dir} is empty, "
#                          f"using default tokenizer i.e. {self.WORDS} words = {self.TOKENS} tokens")
#             self.tokenizer = None

#     def count_tokens(self, text):
#         if self.tokenizer is not None:
#             return len(self.tokenizer.encode(text))
#         else:
#             return int(math.ceil((self.TOKENS/self.WORDS) * len(text.split())))
    
# _tokenizer = CustomTokenizer(globals.TOKENIZER)    

# def count_tokens(text: str) -> int:
#     global _tokenizer
#     return _tokenizer.count_tokens(text)



# class CustomTokenizer:    
#     """A custom tokenizer class"""
#     TOKENS: int = 1000
#     WORDS: int = 750

#     def __init__(self, bucket, prefix, local_dir):
#         print(f"CustomTokenizer, based on HF transformers")
#         # Check if the tokenizer files exist in s3 and if not, use the autotokenizer       
#         _download_from_s3(bucket, prefix, local_dir)
#         # Load the tokenizer from the local directory
#         dir_not_empty = any(Path(local_dir).iterdir())
#         if dir_not_empty is True:
#             logger.info("loading the provided tokenizer")
#             self.tokenizer = AutoTokenizer.from_pretrained(local_dir)
#         else:
#             logger.error(f"no tokenizer provided, the {local_dir} is empty, "
#                          f"using default tokenizer i.e. {self.WORDS} words = {self.TOKENS} tokens")
#             self.tokenizer = None

#     def count_tokens(self, text):
#         if self.tokenizer is not None:
#             return len(self.tokenizer.encode(text))
#         else:
#             return int(math.ceil((self.TOKENS/self.WORDS) * len(text.split())))
    
# _tokenizer = CustomTokenizer(globals.READ_BUCKET_NAME, globals.TOKENIZER_DIR_S3, globals.TOKENIZER)    