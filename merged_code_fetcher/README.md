# Merged Code Fetcher

A unified web application that combines Netflix and ChatGPT verification code fetching with comprehensive admin panel for key management.

## Features

### User Features
- **Netflix Code Fetching**: Retrieve 4-digit Netflix verification codes from email
- **ChatGPT Code Fetching**: Retrieve 6-digit ChatGPT verification codes from multiple email accounts
- **Service Selection**: Choose between Netflix or ChatGPT services
- **Real-time Key Validation**: Instant validation of API keys
- **Responsive Design**: Works on desktop and mobile devices

### Admin Features
- **API Key Management**: Create, activate/deactivate, and delete API keys
- **Usage Limits**: Set usage limits per key (1-1000 uses)
- **Expiration Dates**: Set expiration dates for keys (1 day to 1 year)
- **Bulk Key Creation**: Generate multiple keys at once
- **Usage Analytics**: Dashboard with usage statistics and charts
- **Detailed Logging**: Track all key usage with timestamps and IP addresses
- **Key Details**: View detailed information about each key including usage history
- **Password Management**: Change admin password securely

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/merged-code-fetcher.git
cd merged-code-fetcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (create a `.env` file):
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///code_fetcher.db
IMAP_SERVER=imap.gmail.com
EMAIL_ACCOUNT=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

4. Run the application:
```bash
python app.py
```

5. Access the application:
- User interface: http://localhost:5000
- Admin panel: http://localhost:5000/admin (default login: admin/admin123)

## Usage

### For Users
1. Navigate to the homepage
2. Select either Netflix or ChatGPT service
3. Enter your valid API key
4. Click "Get Code" to retrieve the verification code

### For Admins
1. Navigate to the admin login page
2. Log in with admin credentials
3. Use the dashboard to monitor system usage
4. Create new API keys with custom usage limits
5. Manage existing keys (activate/deactivate/delete)
6. View detailed usage logs

## API Endpoints

### User Endpoints
- `GET /` - Homepage with service selection
- `GET /netflix` - Netflix code fetching page
- `GET /chatgpt` - ChatGPT code fetching page
- `POST /get-code` - Fetch verification code (requires valid key)
- `POST /validate-key` - Validate API key (real-time)

### Admin Endpoints
- `GET /admin/login` - Admin login page
- `GET /admin` - Admin dashboard
- `GET /admin/keys` - Manage API keys
- `GET /admin/keys/create` - Create new API key
- `GET /admin/keys/<id>` - View key details
- `GET /admin/usage-logs` - View usage logs
- `GET /admin/settings` - Admin settings

## Security

- All API keys are stored securely in the database
- Admin passwords are hashed using Werkzeug security
- Usage is tracked with IP addresses for security monitoring
- Keys can be deactivated or deleted immediately if compromised
- Usage limits prevent abuse of the system

## Database Schema

### Admin Users
- `id` - Primary key
- `username` - Admin username
- `password_hash` - Hashed password
- `created_at` - Account creation timestamp
- `is_active` - Account status

### API Keys
- `id` - Primary key
- `key` - Unique API key string
- `service_type` - 'netflix', 'chatgpt', or 'both'
- `usage_limit` - Maximum number of uses
- `current_usage` - Current usage count
- `created_at` - Key creation timestamp
- `expires_at` - Expiration timestamp (nullable)
- `is_active` - Key status
- `created_by` - Admin user ID (foreign key)

### Usage Logs
- `id` - Primary key
- `key_id` - API key ID (foreign key)
- `service_used` - 'netflix' or 'chatgpt'
- `timestamp` - Usage timestamp
- `ip_address` - User IP address
- `success` - Success status
- `error_message` - Error details (if failed)

## Customization

### Styling
- Modify `static/style.css` to change the look and feel
- Update colors and fonts to match your branding

### Email Configuration
- Update email credentials in the `.env` file
- Add additional email accounts in `email_reader.py` for ChatGPT

### Service Configuration
- Modify `email_reader.py` to adjust email parsing logic
- Update regex patterns for code extraction if needed

## Troubleshooting

### Common Issues
1. **Email not received**: Check spam/junk folders
2. **Invalid key**: Ensure key is active and not expired
3. **Usage limit exceeded**: Create a new key or reset usage count
4. **Database errors**: Ensure database file has write permissions

### Logs
- Check console output for Flask logs
- View usage logs in admin panel for detailed error information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on the GitHub repository or contact the maintainers.
