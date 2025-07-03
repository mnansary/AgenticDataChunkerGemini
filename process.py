import argparse
import json
import os
import csv
from pathlib import Path
from tqdm import tqdm

# Assuming your agenticchunker library is installed and accessible
from agenticchunker.llm import call_llm
from agenticchunker.prompt import chunk_config, create_contextual_prompt, background_prompt, action_prompt
from agenticchunker.utils import read_markdown, save_dict_to_json

def process_single_file(markdown_path: Path, output_dir: Path):
    """
    Processes a single markdown file, generates JSON, and saves it.

    Args:
        markdown_path (Path): The path to the input markdown file.
        output_dir (Path): The directory where the output JSON should be saved.

    Returns:
        tuple: A tuple containing (bool, str). 
               (True, "") on success.
               (False, "error message") on failure.
    """
    try:
        # 1. Read the markdown content
        markdown_content = read_markdown(markdown_path)
        
        # 2. Generate the final, context-aware prompt
        final_action_prompt = create_contextual_prompt(str(markdown_path), action_prompt)
        
        # 3. Combine with background and markdown for the full LLM input
        full_prompt = background_prompt + final_action_prompt + markdown_content
        
        # 4. Call the LLM
        response = call_llm(full_prompt, chunk_config)
        
        # 5. Parse the JSON response
        data = json.loads(response)
        
        # 6. Save the output
        output_filename = markdown_path.stem + ".json"
        output_path = output_dir / output_filename
        save_dict_to_json(data, output_path)
        
        return True, ""

    except json.JSONDecodeError as e:
        error_message = f"Failed to parse LLM response as JSON. Error: {e}. Response was: {response[:200]}..."
        return False, error_message
    except FileNotFoundError as e:
        error_message = f"Input file not found. Error: {e}"
        return False, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return False, error_message


def main():
    """
    Main function to parse arguments and process a directory of markdown files.
    """
    parser = argparse.ArgumentParser(
        description="Process a directory of markdown files to generate structured JSON using an LLM.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Path to the directory containing the input .md files."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Path to the directory where the output .json files and error.csv will be saved."
    )
    # --- NEW FEATURE: --force flag ---
    parser.add_argument(
        "--force",
        action="store_true", # Makes it a flag, e.g., --force
        help="Force reprocessing of all files, even if the output JSON already exists."
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_files = list(input_dir.glob("*.md"))

    if not markdown_files:
        print(f"No markdown files (.md) found in {input_dir}")
        return

    print(f"Found {len(markdown_files)} markdown files to process.")
    
    error_log_path = output_dir / "error.csv"
    failed_files = []
    # --- NEW: Counter for skipped files ---
    skipped_count = 0

    with open(error_log_path, 'w', newline='', encoding='utf-8') as csvfile:
        error_writer = csv.writer(csvfile)
        error_writer.writerow(['failed_file_path', 'error_message'])
        
        for md_path in tqdm(markdown_files, desc="Processing files"):
            # --- NEW: Check if output file already exists ---
            output_filename = md_path.stem + ".json"
            output_path = output_dir / output_filename

            if not args.force and output_path.exists():
                skipped_count += 1
                continue # Skip to the next file in the loop
            # --- END of new check ---

            success, message = process_single_file(md_path, output_dir)
            if not success:
                # Use tqdm.write to print without disturbing the progress bar
                tqdm.write(f"\nERROR processing {md_path.name}: {message}")
                failed_files.append((str(md_path), message))
                error_writer.writerow([str(md_path), message])

    # --- UPDATED: Final summary report ---
    total_processed = len(markdown_files) - skipped_count
    successful_count = total_processed - len(failed_files)
    
    print("\n" + "="*30)
    print("Processing Complete.")
    print(f"Total files found: {len(markdown_files)}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Successfully processed: {successful_count}")
    print(f"Failed to process: {len(failed_files)}")
    print(f"Output JSONs saved in: {output_dir}")
    if failed_files:
        print(f"Details for failed files saved in: {error_log_path}")
    print("="*30)


if __name__ == "__main__":
    main()