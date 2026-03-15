# Retail AI Shopping Assistant

An intelligent retail assistant that helps users find products, receive recommendations, and make purchases through a convenient conversational interface.

## Project Description

This project implements an AI-powered shopping assistant that uses natural language processing to provide personalized recommendations. The assistant integrates with the Odoo system to access the product catalog and manage orders.

## Key Features

* Product search using natural language queries
* Personalized product recommendations
* Shopping cart management
* Order placement
* User authentication
* Conversational interface for natural interaction

## Technical Specifications

* Use of *OpenAI API* for natural language processing
* Integration with Odoo via JSON-RPC
* Local database for storing sessions and interaction history
* *RAG (Retrieval-Augmented Generation)* to improve responses using context
* Pydantic models for data validation

## Requirements

* Python 3.8+
* Dependencies listed in `requirements.txt`
* Access to the OpenAI API (API key required)
* Access to the Odoo API (if needed)

## Installation

1. Clone the repository:

```bash
git clone [repository URL]
cd retail-pydantic-ai
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the required environment variables:

```
OPENAI_API_KEY=your_openai_key
ODOO_URL=https://your_odoo_server/api
ODOO_DB=database_name
ODOO_USERNAME=username
ODOO_PASSWORD=password
```

## Usage

### Using Python

Run the main module:

```bash
python main.py
```

Enable debug mode:

```bash
python main.py --debug
```

### Using the run.sh script

For convenience, a `run.sh` script was created to easily launch the agent with different parameters:

```bash
# Make the script executable (run once)
chmod +x run.sh

# Launch in normal mode
./run.sh

# Launch in debug mode
./run.sh --debug
# or
./run.sh -d

# Specify a custom log file
./run.sh --log custom.log
# or
./run.sh -l custom.log

# Show help
./run.sh --help
# or
./run.sh -h
```

The `run.sh` script performs additional checks before launching:

* Checks for Python 3
* Checks for the `.env` file and warns if missing
* Checks for all dependencies from `requirements.txt` and offers to install them
* Checks for the presence of the main file `main.py`

## Project Structure

* `main.py` — Main module to launch the assistant
* `agent.py` — Implementation of the query-processing agent
* `models.py` — Pydantic data models
* `odoo_api.py` — Integration with Odoo API
* `database.py` — Database operations
* `rag.py` — RAG implementation for improved responses
* `config.py` — Project configuration
* `utils.py` — Helper functions

## Testing

To run tests:

```bash
pytest
```
