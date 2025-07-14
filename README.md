# Remnawave Admin Bot

Telegram bot for managing Remnawave proxy service.

## Features

- User management (create, update, delete, search)
- Node management (view, enable, disable, restart)
- System statistics
- Host management
- Inbound management
- Bulk operations
- HWID device management

## Installation

1. Clone the repository
2. Install dependencies:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`
3. Copy `.env.example` to `.env` and fill in your API credentials
4. Run the bot:
   \`\`\`
   python main.py
   \`\`\`

## Environment Variables

- `API_BASE_URL`: Base URL for the Remnawave API
- `REMNAWAVE_API_TOKEN`: Your Remnawave API token
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `ADMIN_USER_IDS`: Comma-separated list of Telegram user IDs that can access the bot

## Usage

1. Start the bot by sending `/start` command
2. Navigate through the menus to manage users, nodes, and other features
3. Use the search functionality to find specific users

## User Management

- View all users
- Search users by username, UUID, Telegram ID, email, or tag
- Create new users
- Edit user details
- Enable/disable users
- Reset user traffic
- Revoke user subscription
- Manage user HWID devices
- View user statistics

## Node Management

- View all nodes
- View node details
- Enable/disable nodes
- Restart nodes
- View node statistics

## System Statistics

- View general system statistics
- View bandwidth statistics
- View node statistics

## Host Management

- View all hosts
- View host details
- Enable/disable hosts
- Edit host details
- Delete hosts

## Inbound Management

- View all inbounds
- View inbound details
- Add inbound to all users
- Remove inbound from all users
- Add inbound to all nodes
- Remove inbound from all nodes

## Bulk Operations

- Reset traffic for all users
- Delete inactive users
- Delete expired users
- Bulk update users

## License

This project is licensed under the MIT License - see the LICENSE file for details.
