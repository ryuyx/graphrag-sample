# Multi-Workspace GraphRAG Setup

This setup allows you to manage multiple isolated knowledge bases (workspaces) using a single GraphRAG installation and configuration.

## Directory Structure

Create a folder for each workspace inside the `workspaces/` directory. Each workspace must have an `input/` folder containing your source documents.

Example:
```
graphrag-sample/
├── main_multi_workspace.py  <-- The new script
├── settings.yaml            <-- Shared configuration (LLM settings, prompts)
├── .env                     <-- Shared API keys
└── workspaces/
    ├── project_alpha/       <-- Workspace 1
    │   └── input/           <-- Put text files here
    │       ├── doc1.txt
    │       └── doc2.txt
    └── project_beta/        <-- Workspace 2
        └── input/
            └── data.txt
```

## Usage

### 1. Prepare a Workspace
Create a directory in `workspaces/` (e.g., `my_new_project`) and create an `input` folder inside it with your text files.

### 2. Run Indexing
To build the knowledge graph for a specific workspace, run:

```bash
python multi_workspace_main.py --workspace my_new_project --index
```

This will generate `output/`, `cache/`, and `logs/` inside `workspaces/my_new_project/`.

### 3. Run Search
To query the knowledge graph for a specific workspace, run:

```bash
python multi_workspace_main.py --workspace my_new_project
```

You can then perform Global, Local, Drift, or Basic searches isolated to that workspace's data.

## Configuration

The `settings.yaml` in the root directory is used as the base configuration. The script automatically overrides the storage paths to point to the selected workspace folder.

If you need workspace-specific prompts, you would need to further modify the script to update prompt paths in the config object similarly to how storage paths are updated.
