import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import gradio as gr

# --- Load dataset ---
books_path = r"C:/Users/MSI/Desktop/Book Sphere/data/books_with_categories.csv"
books = pd.read_csv(books_path)

# Ensure thumbnails exist
books["large_thumbnail"] = books["thumbnail"].fillna("cover-not-found.jpg")

# --- Initialize sentence transformer model ---
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Generate embeddings for all book descriptions ---
print("Generating embeddings for all book descriptions...")
book_embeddings = model.encode(books["description"].fillna("").tolist(), show_progress_bar=True)


# --- Semantic search function ---
def retrieve_semantic_recommendations(query, category="All", tone="All", top_k=16):
    # Get embedding for the query
    query_emb = model.encode([query])

    # Compute cosine similarity
    similarities = cosine_similarity(query_emb, book_embeddings)[0]

    # Add similarity scores to DataFrame
    books["similarity"] = similarities

    # Filter by category if needed
    if category != "All":
        filtered_books = books[books["simple_categories"] == category].copy()
    else:
        filtered_books = books.copy()

    # Filter by tone if needed
    if tone != "All":
        if tone == "Happy":
            filtered_books = filtered_books.sort_values(by="joy", ascending=False)
        elif tone == "Surprising":
            filtered_books = filtered_books.sort_values(by="surprise", ascending=False)
        elif tone == "Angry":
            filtered_books = filtered_books.sort_values(by="anger", ascending=False)
        elif tone == "Suspenseful":
            filtered_books = filtered_books.sort_values(by="fear", ascending=False)
        elif tone == "Sad":
            filtered_books = filtered_books.sort_values(by="sadness", ascending=False)

    # Sort by semantic similarity
    filtered_books = filtered_books.sort_values(by="similarity", ascending=False)

    # Return top_k books
    return filtered_books.head(top_k)


# --- Gradio interface ---
def recommend_books(query, category, tone):
    recs = retrieve_semantic_recommendations(query, category, tone)
    results = []
    for _, row in recs.iterrows():
        desc_trunc = " ".join(str(row["description"]).split()[:38]) + "..."
        authors = str(row["authors"])
        caption = f"{row['title']} by {authors}: {desc_trunc}"
        results.append((row["large_thumbnail"], caption))
    return results


categories = ["All"] + sorted(books["simple_categories"].dropna().unique())
tones = ["All", "Happy", "Surprising", "Angry", "Suspenseful", "Sad"]

with gr.Blocks(theme=gr.themes.Glass()) as dashboard:
    gr.Markdown("# Semantic Book Recommender")
    with gr.Row():
        user_query = gr.Textbox(label="Enter a book description:",
                                placeholder="e.g., A story about friendship and adventure")
        category_dropdown = gr.Dropdown(choices=categories, label="Select category:", value="All")
        tone_dropdown = gr.Dropdown(choices=tones, label="Select emotional tone:", value="All")
        submit_button = gr.Button("Find Recommendations")
    output = gr.Gallery(label="Recommended books", columns=4, rows=2)

    submit_button.click(fn=recommend_books, inputs=[user_query, category_dropdown, tone_dropdown], outputs=output)

if __name__ == "__main__":
    dashboard.launch()

