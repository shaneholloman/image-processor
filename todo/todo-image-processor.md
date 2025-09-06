# Image Processor Project Kanban Board

## To Do

[next](../plans/consolidate-tools-plan.md)

Make sure the repo rename on GitHub that I made is reflected locally and is not causing any sync issues.

### Documentation

- [ ] Write a README.md file with setup and usage instructions
- [ ] Document any configuration options and environment variables
- [ ] Add information about Ollama API interaction

### Optimization and Error Handling

- [ ] Implement retry mechanism for failed API calls (if needed)
- [ ] Optimize for performance (e.g., batch processing, if applicable)

## In Progress

## Backlog (Future Enhancements)

- [ ] Add support for additional image formats
- [ ] Implement multi-threading for faster processing
- [ ] Add option to export results to CSV or JSON
- [ ] Add support for custom Ollama models
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
- [ ] Implement a function to completely strip all metadata (nuclear option)
- [ ] Develop a function to analyze and report dominant hues in images
- [ ] Extend functionality to edit metadata in raw camera files and DNG files
- [ ] Research and implement best practices for metadata fields:
  - [ ] Investigate compatibility issues with apps like Darktable
  - [ ] Optimize metadata field usage for LLM output
  - [ ] Ensure proper handling of multi-paragraph descriptions

> Consider TypeScript versions for each toolset.
