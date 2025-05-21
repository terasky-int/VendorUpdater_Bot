# Gmail OAuth2 Setup Instructions

To use OAuth2 authentication with Gmail, follow these steps:

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Gmail API for your project

2. **Create OAuth2 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Name your client and click "Create"
   - Download the credentials JSON file

3. **Save the Credentials File**:
   - Rename the downloaded file to `credentials.json`
   - Place it in the root directory of this project

4. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

5. **Run the Application**:
   - The first time you run the application, it will open a browser window asking you to authorize the application
   - After authorization, a token will be saved locally for future use

## Note
The token is stored in `token.pickle` and will be used for subsequent runs until it expires.