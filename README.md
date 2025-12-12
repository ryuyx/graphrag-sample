# GraphRAG MVP Sample

This is a Minimum Viable Product (MVP) sample for Microsoft GraphRAG.

## Prerequisites

- Python 3.10+
- OpenAI API Key

## Setup

1. **Install Dependencies**
   Ensure you have `uv` installed, then run:
   ```bash
   uv pip install graphrag python-dotenv
   ```

2. **Configure API Key**
   Open the `.env` file and replace `<API_KEY>` with your actual OpenAI API Key.
   ```dotenv
   GRAPHRAG_API_KEY=sk-your-api-key-here
   ```

3. **Input Data**
   Sample data is located in `input/sample.txt`. You can add more text files to this directory.

## Running the Sample

Run the `main.py` script to execute the GraphRAG pipeline (Indexing -> Querying).

```bash
python main.py
```

## What it does

1. **Indexing**: Processes text files in `input/` to build a knowledge graph.
2. **Global Search**: Performs a global query to summarize high-level information.
3. **Local Search**: Performs a local query to find specific details about entities.

## Configuration

You can adjust settings in `settings.yaml`.
