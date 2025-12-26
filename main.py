import asyncio
import os
import sys
import io

# Fix for UnicodeEncodeError on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
from dotenv import load_dotenv

from graphrag.config.load_config import load_config
from graphrag.api.index import build_index
from graphrag.api.query import global_search, local_search, drift_search, basic_search
from graphrag.utils.storage import load_table_from_storage, storage_has_table
from graphrag.utils.api import create_storage_from_config
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.logger.progress import Progress


class PrintProgressCallbacks(NoopWorkflowCallbacks):
    def progress(self, progress: Progress):
        if progress.total_items:
            percent = (progress.completed_items / progress.total_items) * 100
            print(f"[{progress.description}] {progress.completed_items}/{progress.total_items} ({percent:.1f}%)")
        else:
            print(f"[{progress.description}] {progress.completed_items}")

    def workflow_start(self, name: str, instance: object):
        print(f"\nStarting workflow: {name}")

    def workflow_end(self, name: str, instance: object):
        print(f"Completed workflow: {name}")


async def main():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GRAPHRAG_API_KEY")
    if not api_key or api_key == "<API_KEY>":
        print("⚠️  WARNING: GRAPHRAG_API_KEY is not set correctly in .env file.")
        print("Please edit .env and add your OpenAI API Key.")
        print("File: " + str(Path.cwd() / ".env"))
        return

    print("🚀 Starting GraphRAG MVP Use Case")
    root_dir = Path.cwd()
    print(f"Working Directory: {root_dir}")

    # Load config
    config = load_config(root_dir)

    # 1. Indexing
    # Indexing creates the knowledge graph from input/
    print("\n--- Step 1: Indexing Data ---")
    await build_index(config=config, verbose=True, callbacks=[PrintProgressCallbacks()])

    # Load tables for search
    print("\n--- Loading data for search ---")
    # We assume single output storage as per settings.yaml
    storage_obj = create_storage_from_config(config.output)
    
    # Helper to load table
    async def load_df(name):
        return await load_table_from_storage(name=name, storage=storage_obj)

    # Load required dataframes
    print("Loading entities...")
    entities = await load_df("entities")
    print("Loading communities...")
    communities = await load_df("communities")
    print("Loading community_reports...")
    community_reports = await load_df("community_reports")
    print("Loading text_units...")
    text_units = await load_df("text_units")
    print("Loading relationships...")
    relationships = await load_df("relationships")
    
    covariates = None
    if await storage_has_table("covariates", storage_obj):
        print("Loading covariates...")
        covariates = await load_df("covariates")

    # Interactive Loop
    while True:
        print("\n" + "="*50)
        user_input = input("Enter your query (or type 'exit' to quit): ").strip()
        if user_input.lower() in ['exit', 'quit', 'q']:
            break
        if not user_input:
            continue

        search_type = input("Select search type (1: Global, 2: Local, 3: Drift, 4: Basic) [Default: 1]: ").strip()
        
        if search_type == '2':
            print(f"\nRunning Local Search for: {user_input}")
            response, context = await local_search(
                config=config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                text_units=text_units,
                relationships=relationships,
                covariates=covariates,
                community_level=2,
                response_type="Multiple Paragraphs",
                query=user_input,
            )
        elif search_type == '3':
            print(f"\nRunning Drift Search for: {user_input}")
            response, context = await drift_search(
                config=config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                text_units=text_units,
                relationships=relationships,
                community_level=2,
                response_type="Multiple Paragraphs",
                query=user_input,
            )
        elif search_type == '4':
            print(f"\nRunning Basic Search for: {user_input}")
            response, context = await basic_search(
                config=config,
                text_units=text_units,
                query=user_input,
            )
        else:
            print(f"\nRunning Global Search for: {user_input}")
            response, context = await global_search(
                config=config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                community_level=2,
                dynamic_community_selection=False,
                response_type="Multiple Paragraphs",
                query=user_input,
            )
        
        print(f"\nResponse:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
