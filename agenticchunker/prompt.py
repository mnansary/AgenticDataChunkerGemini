

from pydantic import BaseModel, Field
from typing import List
from google.genai import types

from pydantic import BaseModel, Field
from typing import List

import re

def create_contextual_prompt(markdown_filepath, action_prompt_template):
    """
    Extracts the main topic from the filename and injects it into the prompt.
    """
    # Example filename: 'bengalmeat.com_beef_beef-bone-in.md'
    # Extracts 'beef-bone-in'
    try:
        # This regex looks for the last part of the filename after the last underscore,
        # removes the '.md' extension, and replaces hyphens with spaces.
        topic_slug = re.search(r'_([^_]+)\.md$', markdown_filepath).group(1)
        main_topic = topic_slug.replace('-', ' ')
    except AttributeError:
        # Fallback if the filename format is unexpected
        main_topic = "the product on this page"

    # Inject the extracted topic into the prompt template
    return action_prompt_template.replace("[PRIMARY_SUBJECT_PLACEHOLDER]", main_topic)


class ProcessedChunk(BaseModel):
    """
    A processed, self-contained chunk of text optimized for RAG,
    with extracted metadata.
    """
    chunk_title: str = Field(..., description="A short, descriptive title for the text chunk, summarizing its core topic.")
    chunk_text: str = Field(..., description="A self-contained and coherent paragraph of text, rewritten for clarity and completeness. It should be able to stand alone and be fully understandable without external context.")
    keywords: List[str] = Field(..., description="A list of key terms, product names, or topics present in the chunk_text.")

class ProcessedPage(BaseModel):
    """A structured representation of a webpage, broken down into multiple self-contained chunks."""
    chunks: List[ProcessedChunk] = Field(..., description="A list of all processed, self-contained chunks extracted from the webpage.")


chunk_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=ProcessedPage, # Use the new list-based schema
    temperature=0.2,
    max_output_tokens=8192 # Increased to handle potentially large pages with many chunks
)

background_prompt = """
You are a data processing agent for a cutting-edge RAG (Retrieval-Augmented Generation) system.
Your current task is to process web pages from 'Bengal Meat', a Bangladeshi company that is a pioneer in the meat processing industry.
Your outputs will form the knowledge base of this RAG system, so the quality, accuracy, and self-sufficiency of each chunk are of paramount importance.
Key information about Bengal Meat:
- **Mission**: To be a leading provider of safe, hygienic, and 100% Halal meat and meat products for both local and international markets.
- **History**: Established in 2006, it was the country's first international standard abattoir.
- **Core Strengths**: They emphasize a rigorous quality control process, from livestock sourcing and Halal slaughtering to processing and distribution, maintaining a cold chain to preserve freshness and nutritional value.
- **Product Range**: They offer a wide variety of fresh meat cuts (beef, mutton, chicken) and processed products like sausages, salami, and snacks.
- **Service Area**: They primarily serve Dhaka, Chattogram, and Sylhet through a network of butcher shops and online delivery.
Your goal is to convert raw, messy markdown text from their website into clean, self-contained, and informative chunks suitable for a vector database. These chunks must be factually pristine.
"""

action_prompt = """
You will be given text from a single webpage. Your task is to analyze this text and break it down into a list of logical, self-contained chunks. For each chunk, you must strictly adhere to the following instructions.

***Golden Rules of Processing:***
1.  **MAINTAIN FACTUAL ACCURACY**: This is your highest priority. All critical data (prices, weights, quantities, dates, names) must be preserved exactly. Do not alter, add, or omit this data.
2.  **NO FABRICATION**: You are strictly forbidden from inventing information. If the text is ambiguous, represent it as-is without making assumptions.
3.  **CREATE SELF-SUFFICIENT CHUNKS**: Each chunk must be fully understandable on its own, without needing external context from other chunks.
4.  **GUARANTEE COMPLETENESS**: A chunk must be a complete thought. It cannot end abruptly or mid-sentence.
5.  **NO INFORMATION LEFT BEHIND**: This is critical. You must process the *entire document*. Every piece of information in the source text must be captured in a relevant chunk. Do not discard sections.
6.  **CREATE LARGE, COMPREHENSIVE CHUNKS**: Your goal is to make each chunk as large and informative as possible, up to a limit of ~2000 words, while maintaining a single, coherent topic. **You must consolidate related sub-topics into one chunk instead of splitting them.**

***Processing Workflow:***

**Step 1: Analyze and Define Chunk Boundaries**
- Your default strategy is to **consolidate, not split**.
- A "topic" should be interpreted broadly. For example, if a page describes a product, you must **merge all related information**—such as its primary description, detailed specifications, price, quantity, nutritional facts, and cooking instructions—into a **single, unified chunk** for that product.
- Only create a new chunk when the topic **fundamentally changes**. For instance:
    - **Chunk 1:** A comprehensive description of "Beef Bone-In".
    - **Chunk 2:** A recipe for "Beef Stir Fry".
    - **Chunk 3:** A recipe for "Beef Chili Onion".
    - **Chunk 4:** A summary of "Related Products".

**Step 2: Rewrite and Refine Each Chunk**
- For each identified topic, gather all its related text fragments from anywhere on the page.
- Rewrite the combined information into a single, seamless, and descriptive text block. Convert all bullet points, lists, and messy formatting into clean, readable prose.
- Ensure the final chunk text flows logically and is easy to read, even if it is very long.

**Step 3: Extract Metadata for Each Chunk**
- **`chunk_title`**: Create a short, accurate title that reflects the entire consolidated topic (e.g., "Product Details: Beef Bone-In", "Recipe: Beef Stir Fry", "Related Product Recommendations").
- **`keywords`**: Extract key terms from the final, large chunk text.

***MANDATE:*** Process the following markdown text. Your output must be a JSON object containing a list named "chunks". Follow the consolidation strategy to make chunks as large and comprehensive as the topic allows.
"""