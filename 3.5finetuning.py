import openai
import time
import os
import tomli
from pathlib import Path

# Load configuration from TOML file
config_path = Path("config.toml")
config = {}

if config_path.exists():
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    
    # Set OpenAI API key from config
    openai.api_key = config["openai"]["api_key"]
else:
    # Fallback to environment variable
    openai.api_key = os.environ.get("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable or create a config.toml file.")

# Get configuration parameters or use defaults
model = config.get("fine_tuning", {}).get("model", "gpt-3.5-turbo")
n_epochs = config.get("fine_tuning", {}).get("n_epochs", 4)
training_file = config.get("fine_tuning", {}).get("training_file", "training_data.jsonl")
check_interval = config.get("logging", {}).get("check_interval", 60)

# Upload training file
upload_response = openai.File.create(
    file=open(training_file, "rb"),
    purpose="fine-tune"
)
file_id = upload_response["id"]
print(f"File uploaded. File ID: {file_id}")

# Fine tuning
fine_tune_response = openai.FineTune.create(
    training_file=file_id,
    model=model, 
    n_epochs=n_epochs
)
print(f"Fine-tuning job started. Job ID: {fine_tune_response['id']}")

# Monitor job status
job_id = fine_tune_response["id"]
while True:
    status = openai.FineTune.retrieve(id=job_id)
    print(f"Current status: {status['status']}")
    if status["status"] in ["succeeded", "failed"]:
        break
    time.sleep(check_interval)


