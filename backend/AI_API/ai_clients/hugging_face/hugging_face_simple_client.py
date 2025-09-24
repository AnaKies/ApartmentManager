from transformers import pipeline

# 2. Load a pre-trained text generation pipeline
generator = pipeline("text-generation", model="gpt4")

# 3. Provide a prompt
prompt = "Near the table is "

# 4. Generate text
outputs = generator(prompt, max_length=50, num_return_sequences=1)

# 5. Print the generated text
for output in outputs:
    print(output["generated_text"])