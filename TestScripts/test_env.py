# test_env.py

# --- Test pandas ---
import pandas as pd

df_test = pd.DataFrame({
    "Name": ["Alice", "Bob"],
    "Age": [25, 30]
})
print("Pandas test:")
print(df_test, "\n")

# --- Test langchain ---
from langchain.text_splitter import RecursiveCharacterTextSplitter

text = "This is a test. We will split this text into chunks."
splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0)
chunks = splitter.split_text(text)
print("Langchain test:")
print(chunks, "\n")

# --- Test gradio ---
import gradio as gr

def greet(name):
    return f"Hello {name}!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")
print("Gradio test: launching interface...")
demo.launch()
