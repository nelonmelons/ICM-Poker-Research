import openai
import time
import os

# Load API key from environment variable instead of hardcoding
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

upload_response = openai.File.create(
    file=open("training_data.jsonl", "rb"),
    purpose="fine-tune"
)
file_id = upload_response["id"]
print("File uploaded. File ID:", file_id)

#fine tuning
fine_tune_response = openai.FineTune.create(
    training_file=file_id,
    model="gpt-3.5-turbo", 
    n_epochs=4  # Adjust the number of epochs based on the size and complexity of your data
)
print("Fine-tuning job started. Job ID:", fine_tune_response["id"])

job_id = fine_tune_response["id"]
while True:
    status = openai.FineTune.retrieve(id=job_id)
    print("Current status:", status["status"])
    if status["status"] in ["succeeded", "failed"]:
        break
    time.sleep(60)  # Check every minute


