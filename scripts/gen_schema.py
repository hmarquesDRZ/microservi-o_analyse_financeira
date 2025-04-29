import json
import pathlib
import sys

# Ensure the schemas directory is in the Python path
# This assumes the script is run from the project root
ROOT_DIR = pathlib.Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

try:
    from schemas.analysis import AnalysisResponse
except ImportError:
    print("Error: Could not import AnalysisResponse from schemas.analysis.")
    print(f"Please ensure schemas/analysis.py exists and the script is run from the project root ({ROOT_DIR})")
    sys.exit(1)

# Define output path
output_dir = ROOT_DIR / "assistant_config"
output_file = output_dir / "analysis_function.json"

# Create output directory if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)

# Generate the JSON schema from the Pydantic model
schema = AnalysisResponse.model_json_schema()

# Save the schema to the specified file
try:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"Successfully generated JSON schema at: {output_file}")
except IOError as e:
    print(f"Error writing JSON schema file: {e}")
    sys.exit(1) 