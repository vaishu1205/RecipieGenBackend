# Personalized Recipe Generator - Backend

A Django-based backend service that generates personalized recipes using Google's Gemini AI, taking into account dietary restrictions, preferred cuisines, and available ingredients.

## Features

- Generate personalized recipes using AI
- Consider dietary restrictions and preferences
- Support for various cuisines
- Ingredient-based recipe suggestions
- RESTful API endpoints
- Recipe storage and retrieval

## Tech Stack

- Django 5.1
- Django REST Framework
- Google Gemini AI
- SQLite Database
- CORS support for frontend integration

## API Endpoints

- `POST /api/generate/`: Generate a new personalized recipe
- `GET /api/recipes/`: List all generated recipes
- `GET /api/recipes/<id>/`: Retrieve a specific recipe

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd recipe_generator-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root and add:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

5. Run database migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Usage

### Generate Recipe
```bash
POST /api/generate/
Content-Type: application/json

{
    "dietary_restrictions": ["vegetarian", "gluten-free"],
    "preferred_cuisines": ["Italian", "Mexican"],
    "available_ingredients": ["tomatoes", "pasta", "olive oil"]
}
```

### List Recipes
```bash
GET /api/recipes/
```

### Get Specific Recipe
```bash
GET /api/recipes/1/
```

## Security Note

- The current configuration includes CORS settings for local development
- Update CORS settings and SECRET_KEY for production deployment
- Secure the Gemini API key using environment variables

## Development

- The project uses SQLite for development
- CORS is configured for localhost:3000 (default Next.js port)
- Debug mode is enabled by default

## Production Deployment

Before deploying to production:

1. Update `ALLOWED_HOSTS` in settings.py
2. Configure a production-ready database
3. Set `DEBUG = False`
4. Update CORS settings
5. Use environment variables for sensitive data
6. Set up proper static files serving

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 