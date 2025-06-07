import time
from typing import Type
from pydantic import BaseModel
from SimplerLLM.langauge.llm import LLM

from SimplerLLM.tools.json_helpers import (
    extract_json_from_text,
    extract_json,
    convert_json_to_pydantic_model,
    validate_json_with_pydantic_model,
    generate_json_example_from_pydantic
    )


def generate_basic_pydantic_json_model(model_class: Type[BaseModel], prompt: str, llm_instance : LLM, max_retries: int = 3, initial_delay: float = 1.0) -> BaseModel:
    """
    Generates a model instance based on a given prompt, retrying on validation errors.

    :param model_class: The Pydantic model class to be used for validation and conversion.
    :param prompt: The fully formatted prompt including the topic.
    :param llm_instance: Instance of a large language model.
    :param max_retries: Maximum number of retries on validation errors.
    :param initial_delay: Initial delay in seconds before the first retry.
    :return: Tuple containing either (model instance, None) or (None, error message).
    """
    for attempt in range(max_retries + 1):
        try:
            json_model = generate_json_example_from_pydantic(model_class)
            print("json_model：")
            print(json_model)
            optimized_prompt = prompt + f'\n\n.The response   should me a structured JSON format that matches the following JSON: {json_model}'
            print("optimized_prompt:")
            print(optimized_prompt)
            ai_response = llm_instance.generate_text(optimized_prompt)
            print("ai_response:")
            print(ai_response)
            if ai_response:
                json_object = extract_json_from_text(ai_response)
                print("extract_json_from_text:")
                print(json_object)

                validated, errors = validate_json_with_pydantic_model(model_class, json_object)

                if not errors:
                    print("validate_json_with_pydantic_model:")
                    model_object = convert_json_to_pydantic_model(model_class, json_object[0])
                    print("convert_json_to_pydantic_model model_object:")
                    print(model_object)
                    return model_object

        except Exception as e:  # Replace with specific exception if possible
            return f"Exception occurred: {e}"

        if not ai_response and attempt < max_retries:
            time.sleep(initial_delay * (2 ** attempt))  # Exponential backoff
            continue
        elif errors:
            return f"Validation failed after {max_retries} retries: {errors}"
        
        # Retry logic for validation errors
        if errors and attempt < max_retries:
            time.sleep(initial_delay * (2 ** attempt))  # Exponential backoff
            continue
        elif errors:
            return f"Validation failed after {max_retries} retries: {errors}"
        




def generate_pydantic_json_model(model_class: Type[BaseModel], prompt: str, llm_instance : LLM, max_retries: int = 3, initial_delay: float = 1.0) -> BaseModel:
    """
    Generates a model instance based on a given prompt, retrying on validation errors.

    :param model_class: The Pydantic model class to be used for validation and conversion.
    :param prompt: The fully formatted prompt including the topic.
    :param llm_instance: Instance of a large language model.
    :param max_retries: Maximum number of retries on validation errors.
    :param initial_delay: Initial delay in seconds before the first retry.
    :return: Tuple containing either (model instance, None) or (None, error message).
    """
    for attempt in range(max_retries + 1):
        try:
            print("generate_json_example_from_pydantic:")
            json_model = generate_json_example_from_pydantic(model_class)
            #print(model_class)
            #print(json_model)
            optimized_prompt = prompt + f'\n\n.The response should me a structured JSON format that matches the following JSON:: {json_model}'
            ai_response = llm_instance.generate_text(optimized_prompt)
            #print('10')
            #print(ai_response)
            if ai_response:
                print('11')
                ##json_object = extract_json_from_text(ai_response)
                json_object = extract_json(ai_response)
                print('12 extract_json_from_text:')
                #print(json_object)
                validated, errors = validate_json_with_pydantic_model(model_class, json_object)
                print('13 errors:')
                print(errors)
                if not errors:
                    print('14')
                    #print(json_object)
                    #model_object = convert_json_to_pydantic_model(model_class, json_object[0])
                    model_object = convert_json_to_pydantic_model(model_class, json_object)
                    return model_object
                print('15')
        except Exception as e:  # Replace with specific exception if possible
            print('16')
            return f"Exception occurred: {e}"
        print('17')
        if not ai_response and attempt < max_retries:
            time.sleep(initial_delay * (2 ** attempt))  # Exponential backoff
            continue
        elif errors:
            return f"Validation failed after {max_retries} retries: {errors}"
        print('18')
        # Retry logic for validation errors
        if errors and attempt < max_retries:
            time.sleep(initial_delay * (2 ** attempt))  # Exponential backoff
            continue
        elif errors:
            print('19')
            return f"Validation failed after {max_retries} retries: {errors}"
        
             