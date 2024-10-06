import argparse
from tnkos.llm import LLM

def transform_inference_code(original_code: str, model_name: str) -> str:
    llm = LLM()
    
    prompt = f"""
    Transform the following inference code into a class that implements the ModelInterface:

    class ModelInterface:
        def load_model(self) -> None:
            pass

        def unload_model(self) -> None:
            pass

        def run_inference(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
            pass

    The class should be named {model_name} and should:
    1. Implement the load_model method to initialize the model and any necessary components.
    2. Implement the unload_model method to free up resources.
    3. Implement the run_inference method to perform the inference using the input_data.
    4. Use type hints and follow PEP 8 style guidelines.
    5. Handle any necessary error cases.
    6. Store the model in `~/models/` if it has model download code in it.

    Here's the original inference code to transform:

    {original_code}

    Please provide the transformed code that implements the ModelInterface.

    DO NOT YAP. DO NOT PUT IT IN MARKDOWN. ONLY RETURN VALID PYTHON CODE! THANK YOU IN ADVANCE!
    """

    transformed_code = llm.llm_call([{"role": "user", "content": prompt}], {"anthropic": True} )
    return transformed_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform inference code to implement ModelInterface")
    parser.add_argument("src", help="Source file containing the original inference code")
    parser.add_argument("dest", help="Destination file to write the transformed code")
    parser.add_argument("--model-name", default="TransformedModel", help="Name for the transformed model class")
    args = parser.parse_args()

    # Read the source file
    with open(args.src, 'r') as src_file:
        original_code = src_file.read()

    # Transform the code
    transformed_code = transform_inference_code(original_code, args.model_name)

    # Write the transformed code to the destination file
    with open(args.dest, 'w') as dest_file:
        dest_file.write(transformed_code)

    print(f"Transformed code has been written to {args.dest}")
