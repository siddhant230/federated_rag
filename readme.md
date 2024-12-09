# Federated-RAG

Introducing a Federated, encrypted and private Retrieval Augmented Generation pipeline.

## Table of Contents

- [Federated-RAG](#federated-rag)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
  - [How It Works](#how-it-works)
    - [Data Flow](#data-flow)
    - [API Operation Cycle](#api-operation-cycle)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
      - [1. Install SyftBox](#1-install-syftbox)
      - [2. Set Up the Fed-RAG](#2-set-up-the-fed-rag)
  - [Usage](#usage)
    - [Accessing the Web Interface](#accessing-the-web-interface)
    - [Creating the about\_me.json](#creating-the-about_mejson)
    - [Making Query](#making-query)
  - [Contributing](#contributing)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Introduction

Welcome to the Federated RAG app! This project aims to build a encrypted end-to-end RAG flow on top of Syftbox. The projects aims to serve as building block of many downstream use-cases like peer-finder, code-quality-checker, code/project search tool, etc.

## Features

- **Decentralized Architecture**: Eliminates dependency on a central server; every participant runs the API locally.
- **Privacy-Preserving Retrieval**: Individual data remain confidential through homomorphic encryption.
- **Open-source Tools**: The entire pipeline is fuelled by open-source models and workflows.
- **Automated Processing**: The API automatically aggregates info for every participant over the network.
- **SyftBox Integration**: Leverages SyftBox's privacy controls and synchronization capabilities.

## How It Works

1. Expects an  `public/about_me.json` (containing individual information and links to relevant pages)
2. Inbuilt web-scraper for information retrieval.
3. Uses open-source LLM and Embedding model
4. For each user creates a index and store in public folder
5. For a given query makes a multi-query engine through a composed graph.
6. GUI based interaction and result consolidation.

### Data Flow

Each participant's SyftBox directory structure includes:

`SyftBox/Datasites/<your_email>/api_data/fed-rag/`

- _**`public/`**_: Public folder where the API writes the generated responses.

### API Operation Cycle

Every 10 @irina seconds, the Fed-RAG API performs the following tasks:

1. _**Data Scraping**_: Reads about_me JSON file from the `public/` folder, performs web scraping and saves the scraped data to `public/bio.txt`.
2. _**Index creation**_ : The `public/bio.txt` is fetched, converted to index and saved in `public/vector_index`. The vector embeddings are encrypted and saved alongside.
3. _**Query Engine**_: If the user-query is found/input through GUI then -> Retrieval and generation module
   1. _**Embedding Creation**_ : The user query is converted to embedding vector and encrypted through HE.
   2. _**Index Aggregation**_: Aggregates encrypted and stored indexes using homomorphic properties and loads in memory.
   3. _**Retrieval**_: Perform top-k search using the encrypted query embedding and encypted indexes.
   4. _**Generation**_: Top-k fetched indexes are used to fetch corresponding text-blobs which is then put in an local LLM for generation process.

## Getting Started

### Prerequisites

- _**Operating System**_: MacOS or Linux.
- _**SyftBox**_: Installed and set up on your machine.

### Installation

#### 1. Install SyftBox

SyftBox is required to run the Fed-RAG API. Install it by running the following command in your terminal:

```bash
curl -LsSf https://syftbox.openmined.org/install.sh | sh
```

For more information, refer to the [SyftBox Documentation](https://syftbox-documentation.openmined.org/).

#### 2. Set Up the Fed-RAG

After installing SyftBox:

• **Option A: Using Git**

Navigate to your `SyftBox/apis/` directory and clone the Fed-RAG API repository:

```bash
cd ~/Desktop/SyftBox/apis

git clone https://github.com/siddhant230/federated_rag.git
```

• **Option B: Download ZIP**

1. Click below to download the ZIP file of the repository: [Download Repository](https://github.com/siddhant230/federated_rag/archive/refs/heads/main.zip)
2. Extract the ZIP file.
3. Move the extracted fed-rag folder into the `SyftBox/apis/` directory.

SyftBox will automatically detect and install the new API during its execution cycle.

## Usage

### Accessing the Web Interface

@ifra @irina

1. **Open in Browser**: Paste the above URL into your browser’s address bar to access the fed-rag interface.

### Creating the about_me.json

1. Copy and paste this template into your `public/about_me.json`; if not already present, create a new about_me.json in the `public/` folder.
   ```
   {
    "info" : "",
    "links":[],
    "resume_path":""
    }
    ```
2. Fill required information in each of the fields. For example,
   ```
   {
    "info" : "Hi, this is xyz. I work on abcd and my cat name is Mr.CAT",
    "links":[https://github.com/xyz,
            <path_to_twitter>,
            <personal website>...],
    "resume_path":"my_resume.pdf"
    }
    ```

### Making Query

It could be done in two ways:
   1. Through GUI with chat interface.
      - Open the web-app, type in your query and hit enter.
      - The found results and generated responses along with your system performance would be displayed on the web-app.
   2. Using file level interactions
      - @irina


## Contributing

We welcome contributions to enhance the Fed-RAG API:

1. **Fork the Repository**: Click "Fork" on GitHub to create your copy.
2. **Create a Branch**: Develop your feature or fix in a new branch.
3. **Submit a Pull Request**: Provide a detailed description for review.

## License

NA

## Acknowledgments

• **SyftBox**: For providing the platform enabling decentralized applications.
• **Tenseal**: For the homomorphic encryption.
• **OpenMined Community**: Thank you to everyone who has contributed to this project during the [30DaysOfFLCode](https://30daysofflcode.com/) challenge!