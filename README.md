### Banking Assistant

A conversational banking assistant that helps customers check their account balances and related information through a natural language interface.

#### Features

- Secure account authentication flow
- Mobile number-based account lookup
- PIN verification
- Account balance and details retrieval
- Support for IVR and web interfaces

#### Architecture

- **API Layer**: Clean interface for banking API interactions
  - Mock client for development
  - Real client for production use
- **Services Layer**: Business logic independent of API implementation
- **Chat Layer**: Conversation management with OpenAI integration

#### Quick Start

1. **Install Dependencies:**
   ```
   pip install -r requirements.txt --no-deps
   ```

2. **Set Environment Variables:**
   ```
   export OPENAI_API_KEY=your_api_key_here
   export USE_REAL_API=false  # Use "true" for production
   ```

3. **Run the Server:**
   ```
   python server.py
   ```

4. **Run the Client:**
   In a new terminal, run:
   ```
   python client.py
   ```

## Authentication Flow

1. System auto-detects mobile number (in IVR) or asks for it
2. Multiple accounts are retrieved and presented to the user
3. User confirms by providing last 4 digits of account number
4. User authenticates with PIN
5. Account details are displayed

## Switching to Real APIs

To use real banking APIs instead of mock data:
1. Set `USE_REAL_API=true` environment variable
2. Configure API credentials as needed

## Extending

- Add new API methods to `BankingAPIClient` interface
- Implement in both `MockBankingAPIClient` and `RealBankingAPIClient`
- No changes needed to business logic when switching between mock and real APIs
