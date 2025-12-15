
import asyncio
import os
import sys
import io
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Fix for UnicodeEncodeError on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
    parser = argparse.ArgumentParser(description="GraphRAG Multi-Workspace Manager")
    parser.add_argument("--workspace", type=str, required=True, help="Name of the workspace directory")
    parser.add_argument("--index", action="store_true", help="Run indexing before search")
    args = parser.parse_args()

    workspace_name = args.workspace
    run_indexing = args.index

    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GRAPHRAG_API_KEY")
    if not api_key or api_key == "<API_KEY>":
        print("⚠️  WARNING: GRAPHRAG_API_KEY is not set correctly in .env file.")
        return

    root_dir = Path.cwd()
    workspaces_dir = root_dir / "workspaces"
    workspace_path = workspaces_dir / workspace_name
    
    if not workspace_path.exists():
        print(f"❌ Workspace '{workspace_name}' does not exist at {workspace_path}")
        print(f"Please create the directory structure: {workspace_path}/input")
        return

    print(f"🚀 Starting GraphRAG for Workspace: {workspace_name}")
    print(f"Workspace Path: {workspace_path}")

    # Load base config from root
    config = load_config(root_dir)

    # Override paths for isolation
    # 1. Input
    if hasattr(config.input, 'storage'):
        config.input.storage.base_dir = str(workspace_path / "input")
    else:
        config.input.base_dir = str(workspace_path / "input")
    
    # 2. Output
    config.output.base_dir = str(workspace_path / "output")
    
    # 3. Cache
    config.cache.base_dir = str(workspace_path / "cache")
    
    # 4. Reporting (Logs)
    config.reporting.base_dir = str(workspace_path / "logs")
    
    # 5. Vector Store
    if config.vector_store and 'default_vector_store' in config.vector_store:
        # Assuming lancedb for now, update db_uri
        config.vector_store['default_vector_store'].db_uri = str(workspace_path / "output" / "lancedb")

    # Ensure directories exist
    os.makedirs(config.input.storage.base_dir, exist_ok=True)
    os.makedirs(config.output.base_dir, exist_ok=True)
    os.makedirs(config.cache.base_dir, exist_ok=True)
    os.makedirs(config.reporting.base_dir, exist_ok=True)

    # 1. Indexing
    if run_indexing:
        print("\n--- Step 1: Indexing Data ---")
        await build_index(config=config, verbose=True, callbacks=[PrintProgressCallbacks()])

    # Load tables for search
    print("\n--- Loading data for search ---")
    
    # Check if output exists
    if not os.path.exists(config.output.base_dir) or not os.listdir(config.output.base_dir):
        print("❌ Output directory is empty. Please run with --index first.")
        return

    storage_obj = create_storage_from_config(config.output)
    
    # Helper to load table
    async def load_df(name):
        try:
            return await load_table_from_storage(name=name, storage=storage_obj)
        except Exception as e:
            print(f"Warning: Could not load table {name}: {e}")
            return None

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

    if entities is None or communities is None:
        print("❌ Critical tables missing. Please run indexing.")
        return

    # Interactive Loop
    while True:
        print("\n" + "="*50)
        user_input = input(f"[{workspace_name}] Enter your query (or type 'exit' to quit): ").strip()
        if user_input.lower() in ['exit', 'quit', 'q']:
            break
        if not user_input:
            continue

        search_type = input("Select search type (1: Global, 2: Local, 3: Drift, 4: Basic) [Default: 1]: ").strip()
        
        try:
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
                response, context = await drift_search (
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
        except Exception as e:
            print(f"Error during search: {e}")

if __name__ == "__main__":
    asyncio.run(main())
