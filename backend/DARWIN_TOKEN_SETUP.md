# How to Get a National Rail Darwin Token

1. Go to the National Rail Data Feeds registration page:
   https://www.nationalrail.co.uk/100296.aspx

2. Register for an account and request access to the "Darwin" OpenLDBWS feed.

3. Wait for approval. You will receive an email with your unique "AccessToken" (Darwin token).

4. Add your token to your backend `.env` file:
   ```
   DARWIN_TOKEN=your_token_here
   ```

5. Restart your backend server to use the new token.

**Note:**
- The token is required for all SOAP API requests to the Darwin feed.
- Keep your token private and do not share it publicly.
