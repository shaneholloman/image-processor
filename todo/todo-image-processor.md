# Image Processor Project Kanban Board

## To Do

Most immediately, we need to move the image_processor_name tool directory into the source directory of this project and then correctly wire in the configs for each of the tools. Make sure there is a single source of management using a single pyproject.toml file for everything. Also, we need to make sure our two different configs for each of our different tools are using proper pattern-based names that match the tool. Right now, it looks like one of them is using app_config.yaml which is misleading. It should actually match the name of the tool, which it doesn't.

- [meta](../config/app_config.yaml)
- [rename](../image_processor_name/config/rename_config.yaml) That's better, at least it's got "rename" in the file name.

Both of these can be renamed to something more consistent that perfectly matches each of the different tools.

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
