# Appel Workshop

A Django-based level sharing website for Appel where users can upload, share, rate, and complete custom Appel levels.

## Features

- **Level Management**: Upload, edit, and delete custom Appel levels
- **Level Ratings**: Rate levels by difficulty and quality
- **Completion Submissions**: Submit proofs of level completions for verification
- **Admin Triage**: Approve or reject level completion submissions
- **User Profiles**: Customize profiles with display name, country flag, Discord ID, and bio
- **Difficulty Systems**: Support for multiple difficulty rating systems (Punter, Michael Chan, Grassy)
- **Leaderboards**: View user statistics and completion rankings
- **Profanity Filter**: Automatic profanity detection in user-generated content
- **Discord Integration**: 
  - Webhook notifications when levels are completed
  - Difficulty-based emoji reactions
  - Discord user ID pings for verified completions
  - Discord widget on info page

## Installation

### Requirements
- Python 3.8+
- Django 6.0+
- SQLite (or configurable database)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/level_repository.git
cd level_repository
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Collect static files:
```bash
python manage.py collectstatic
```

7. Run the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## Configuration

### Environment Variables

Create a `.env` file in the project root with:

```
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

### Database

By default, SQLite is used. To use a different database, update `DATABASES` in `settings.py`.

## Project Structure

```
level_repository/
├── levels/                          # Main Django app
│   ├── templates/levels/           # HTML templates
│   ├── static/                     # CSS, JavaScript, images
│   ├── migrations/                 # Database migrations
│   ├── models.py                   # Database models
│   ├── views.py                    # View logic
│   ├── forms.py                    # Django forms
│   ├── urls.py                     # URL routing
│   └── admin.py                    # Admin interface
├── level_repository/               # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
└── requirements.txt
```

## Models

### Level
Represents a user-submitted Appel level with difficulty, description, and metadata.

### LevelRating
Stores difficulty and quality ratings from users for each level.

### LevelCompletion
Tracks level completion submissions with proof and approval status.

### Profile
Extended user profile with display name, country, Discord ID, bio, and difficulty system preference.

### Comment
User comments on levels.

## API

The site provides an API for level data. See `/api/docs` for documentation.

## Rules & Guidelines

### Uploading Levels
- Levels must be created by you or credit the original creator
- Levels must have a valid code or Scratch project link
- Levels must be theoretically possible
- No profanity or offensive content

### Verifying Completions
- Verifications must be done in real-time (no TAS)
- Verification must be at 30FPS or higher (minimum 25FPS acceptable)
- Replay codes or video proof required
- Must use the original mod or an approved mod

### Community Standards
- No impersonation or harassment
- Respect copyright
- No hacking or DDoS attempts
- No profanity in comments

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Admin Interface

Access the admin panel at `/admin` with your superuser account to:
- Manage users and profiles
- Review and edit levels
- Moderate ratings and comments
- Triage completion submissions

## Troubleshooting

### Static files not loading
Run `python manage.py collectstatic` and ensure `DEBUG=False` is not set in development.

### Database errors
Run `python manage.py migrate` to apply pending migrations.

### Permission denied errors
Ensure the application has write permissions to the database and `staticfiles` directories.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the project maintainer.

## Authors

- Theme Park Punter (@themadpunter)

## Acknowledgments

- Appel game community
- Django framework
- Bootstrap CSS framework
