import re
import json
from pydantic import BaseModel, ValidationError
from typing import get_type_hints
from pydantic import BaseModel
import inspect
from typing import List, Type, get_origin, get_args



def convert_pydantic_to_json(model_instance):
    """
    Converts a Pydantic model instance to a JSON string.

    Args:
        model_instance (YourModel): An instance of your Pydantic model.

    Returns:
        str: A JSON string representation of the model.
    """
    return model_instance.model_dump_json()


def extract_json(api_response: str) -> str:
    """
    从包含 ```json 标记的 API 响应中提取纯净 JSON 字符串
    :param api_response: API 返回的原始字符串
    :return: 纯净的 JSON 字符串
    """
    # 匹配 ```json{...}``` 模式（含换行符兼容）
    pattern = r'```json(.*?)```'
    match = re.search(pattern, api_response, re.DOTALL)
    json_objects = []
    if match:
        json_str = match.group(1).strip()
        json_obj = json.loads(json_str)
        json_objects.append(json_obj)
        return json_obj  # 提取核心 JSON 并去除首尾空格
    else:
        # 兼容无标记的纯 JSON 情况
        json_str = api_response.strip()
        json_obj = json.loads(json_str)
        json_objects.append(json_obj)
        return json_obj


def extract_json_from_text(text_response):
    # This pattern matches a string that starts with '{' and ends with '}'
    pattern = r'\{[^{}]*\}'

    matches = re.finditer(pattern, text_response)
    json_objects = []

    for match in matches:
        json_str = match.group(0)
        try:
            # Validate if the extracted string is valid JSON
            json_obj = json.loads(json_str)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            # Extend the search for nested structures
            extended_json_str = extend_search(text_response, match.span())
            try:
                json_obj = json.loads(extended_json_str)
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                # Handle cases where the extraction is not valid JSON
                continue

    if json_objects:
        return json_objects
    else:
        return None  # Or handle this case as you prefer

def extend_search(text, span):
    # Extend the search to try to capture nested structures
    start, end = span
    nest_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            nest_count += 1
        elif text[i] == '}':
            nest_count -= 1
            if nest_count == 0:
                return text[start:i+1]
    return text[start:end]

def validate_json_with_pydantic_model(model_class, json_data):
    """
    Validates JSON data against a specified Pydantic model.

    Args:
        model_class (BaseModel): The Pydantic model class to validate against.
        json_data (dict or list): JSON data to validate. Can be a dict for a single JSON object, 
                                  or a list for multiple JSON objects.

    Returns:
        list: A list of validated JSON objects that match the Pydantic model.
        list: A list of errors for JSON objects that do not match the model.
    """
    validated_data = []
    validation_errors = []

    if isinstance(json_data, list):
        for item in json_data:
            try:
                model_instance = model_class(**item)
                validated_data.append(model_instance.dict())
            except ValidationError as e:
                validation_errors.append({"error": str(e), "data": item})
    elif isinstance(json_data, dict):
        try:
            model_instance = model_class(**json_data)
            validated_data.append(model_instance.dict())
        except ValidationError as e:
            validation_errors.append({"error": str(e), "data": json_data})
    else:
        raise ValueError("Invalid JSON data type. Expected dict or list.")

    return validated_data, validation_errors

def convert_json_to_pydantic_model(model_class, json_data):
    #print("Converting JSON to Pydantic model...")
    #print(model_class)
    #print(json_data)
    try:
        model_instance = model_class(**json_data)
        return model_instance
    except ValidationError as e:
        print(f"验证失败: {e.errors()}")  # 输出详细错误
        print("Validation error:", e)
        return None

# Define a function to provide example values based on type
def example_value_for_type(field_type: Type):
    if field_type == str:
        return "example_string"
    elif field_type == int:
        return 0
    elif field_type == float:
        return 0.0
    elif field_type == bool:
        return True
    elif field_type == List[str]:
        return ["generated text 1", "generated text 2"]
    elif field_type == List[int]:
        return [1, 2, 3]
    elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return json.loads(generate_json_example_from_pydantic(field_type))
    # 处理List[BaseModel]类型
    origin_type = get_origin(field_type)
    if origin_type is list:
        item_type = get_args(field_type)[0]
        if inspect.isclass(item_type) and issubclass(item_type, BaseModel):
            return [json.loads(generate_json_example_from_pydantic(item_type)) for _ in range(2)]
        return "Unsupported type"
    else:
        return "Unsupported type"

# Function to generate a JSON example for any Pydantic model
def generate_json_example_from_pydantic(model_class: Type[BaseModel]) -> str:
    print("Generating JSON example from Pydantic model...")
    #print(model_class)
    example_data = {}
    for field_name, field in model_class.__fields__.items():
            field_type = field.annotation
            example_data[field_name] = example_value_for_type(field_type)
   
        
    #print("example_data:")
    #print(example_data)
    try:
        model_instance = model_class(**example_data)
        return model_instance.json()
    except ValidationError as e:
        print(f"Validation error occurred: {e.errors()}")
        return "{}"

