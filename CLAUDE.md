# Banking Assistant Development Guide

## Commands
- **Install Dependencies**: `pip install -r requirements.txt --no-deps`
- **Run Server**: `python server.py`
- **Run Client**: `python client.py`
- **Environment Setup**: 
  ```
  export OPENAI_API_KEY=your_api_key_here
  export USE_REAL_API=false  # Use "true" for production
  ```

## Code Style Guidelines
- **Imports**: Standard lib first, third-party next, internal imports last (relative imports)
- **Types**: Use type hints for all function parameters and returns
- **Naming**: snake_case for variables/functions, CamelCase for classes, UPPER_CASE constants
- **Documentation**: Docstrings for all classes/methods with Args/Returns/Raises sections
- **Error Handling**: Use custom exceptions extending from base exception classes
- **Logging**: Use hierarchical logger names (banking_assistant.module.submodule)
- **Structure**: Follow interface-based architecture with ABC (Abstract Base Classes)
- **Formatting**: 4 spaces indentation, proper spacing between functions/classes
- **Patterns**: Factory pattern for client and tool creation

## Architecture
The codebase follows a layered architecture with API, Services, and Chat layers. Extend functionality by implementing interfaces in the appropriate layer.