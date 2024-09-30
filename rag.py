import supabase
from langchain.embeddings import HuggingFaceEmbeddings
from llama_index.embeddings import LangchainEmbedding

# Supabase Configuration
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_anon_key"

client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# Hugging Face Embeddings Model (replace with your preferred model)
embed_model = LangchainEmbedding(
    HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
)

def generate_embedding(text):
    """Generates an embedding for the given text."""
    return embed_model.embed(query_text=text)

def store_embedding_in_supabase(question_text, embedding):
    """Stores the generated embedding in the Supabase vector database."""
    response = client.table("embeddings").insert({
        "question": question_text,
        "embedding": embedding
    }).execute()
    return response

def process_embeddings(question_data):
    """Processes each question's embedding and stores it in Supabase."""
    for question in question_data:
        question_text = question['question']
        # Generate the embedding for the question text
        embedding = generate_embedding(question_text)
        # Store the embedding in Supabase
        store_embedding_in_supabase(question_text, embedding)
