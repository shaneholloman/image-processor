# Image Processor Project Kanban Board

## To Do

### Documentation

- [ ] Write a README.md file with setup and usage instructions
- [ ] Document any configuration options and environment variables
- [ ] Add information about Ollama API interaction

### Optimization and Error Handling

- [ ] Implement retry mechanism for failed API calls (if needed)
- [ ] Optimize for performance (e.g., batch processing, if applicable)

## In Progress

## Done

### Environment Setup

- [x] Install Miniconda or Anaconda
- [x] Create a new conda environment for the project (image-processor with Python 3.11)
- [x] Activate the conda environment

### Dependencies Installation

- [x] Install required Python packages:
  - [x] requests (for interacting with Ollama API)
  - [x] sqlalchemy (for database operations)
  - [x] tqdm (for progress bars)
  - [x] pyexiv2 (for writing metadata to images)

### Ollama Setup

- [x] Ensure Ollama is installed and running on the system
- [x] Verify that the LLaVA model is available in Ollama

### Database Setup

- [x] Choose SQLite as the database (simple, file-based, cross-platform)
- [x] Create a script to initialize the database schema
- [x] Run database initialization script

### Script Development

- [x] Create main script file
- [x] Implement recursive directory traversal
- [x] Implement logging functionality
- [x] Implement console output
- [x] Implement database insertion
- [x] Implement critical metadata writing to images
- [x] Implement Ollama API interaction for image description
- [x] Refine and test basic script functionality
- [x] Implement file type checking to ignore non-image files
- [x] Ensure support for PNG and JPEG file formats
- [x] Implement proper error handling and logging
- [x] Implement command-line argument parsing for input directory
- [x] Address all Pylance warnings and improve code quality
- [x] Emphasize and improve metadata writing as a core functionality
- [x] Debug and fix Ollama API interaction issues
- [x] Implement streaming response handling for Ollama API
- [x] Add timeout mechanism for API calls

### Testing

- [x] Create a test directory with sample images
- [x] Test each component of the script individually
- [x] Perform an end-to-end test of the entire workflow
- [x] Verify metadata writing for various image formats

- [x] Create initial project plan
- [x] Create basic script structure

## Backlog (Future Enhancements)

- [ ] Implement batch processing for improved performance
- [ ] Add support for additional image formats
- [ ] Create a graphical user interface (GUI)
- [ ] Implement multi-threading for faster processing
- [ ] Add option to export results to CSV or JSON
- [ ] Implement image preprocessing (e.g., resizing, normalization)
- [ ] Add support for custom Ollama models
- [ ] Implement a web interface for remote processing
- [ ] Print txt sidecar file with comprehensive metadata:
  - [ ] Current metadata
  - [ ] Filename
  - [ ] Date edited
  - [ ] Date created
  - [ ] Other relevant metadata
- [ ] Implement tagging system:
  - [ ] Create a tag dictionary for possible tags
  - [ ] Implement logic to create new tags when no suitable tag exists
  - [ ] Ensure tags are lowercase and usually one word (max two words)
- [ ] Add tutorial on opening and editing the database in DBeaver
- [ ] Implement a function to completely strip all metadata (nuclear option)
- [ ] Develop a function to analyze and report dominant hues in images
- [ ] Extend functionality to edit metadata in raw camera files and DNG files
- [ ] Research and implement best practices for metadata fields:
  - [ ] Investigate compatibility issues with apps like Darktable
  - [ ] Optimize metadata field usage for LLM output
  - [ ] Ensure proper handling of multi-paragraph descriptions
