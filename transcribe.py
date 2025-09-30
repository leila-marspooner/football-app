import whisper

# Load the small model (fast to run on CPU)
model = whisper.load_model("small")

# Transcribe your test file
result = model.transcribe("ed.webm")

print("Full transcription result:", result)
print("Just the text:", result["text"])
