# Python Notes

A simple, self-hosted, encrypted notes application built with Flask.

## Features

- **Secure:** Note content is encrypted at rest.
- **CRUD Operations:** Create, view, edit, and delete notes through a clean web interface.
- **Markdown Support:** Notes are rendered from Markdown to HTML, with syntax highlighting for code blocks.
- **Raw View:** View the raw, unformatted text of any note.
- **Authentication:** Protected by simple HTTP Basic Authentication.
- Rate limiting per IP address
- CSRF protection for POST requests
- Configurable via environment variables
- Runs locally or in Docker
- **Easy Setup:** Automatically generates an encryption key on first run.
- **Proxy Friendly:** Designed to work behind a reverse proxy and correctly identify client IPs.

## Getting Started

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/teklynk/notes.git
   cd python_notes
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Rename `sample.env` to `.env`
   - Edit `.env` and set your `SECRET_KEY`, `ALLOWED_DOMAIN`, `HTTP_USER`, and `HTTP_PASS`.

5. **Run the application:**
   ```bash
   python3 python_notes.py
   ```

6. **Deactivate the virtual environment (optional):**
   ```bash
   deactivate
   ```

### Docker Setup

1. **Configure environment variables:**
   - Rename `sample.docker-compose.yml` to `docker-compose.yml`.
   - Edit `docker-compose.yml` and set your `SECRET_KEY`, `ALLOWED_DOMAIN`, `HTTP_USER`, `HTTP_PASS`, and `ENCRYPTION_KEY` under the `environment` section.

2. **Build and run the container:**
   ```bash
   docker-compose up --build -d
   ```

## Notes
- On first local run, the app will generate an `ENCRYPTION_KEY` and save it to the `.env` file if one does not already exist.
- The `ENCRYPTION_KEY` must be a 32-byte, URL-safe, base64-encoded string. The app handles this for you, but it's good to know if you're setting it manually.
- If using Docker, configure environment variables in `docker-compose.yml`. The `.env` file is only used for local development.
- Authentication is optional. If `HTTP_USER` and `HTTP_PASS` are not set, the application will be publicly accessible.
- The app is designed to work behind a reverse proxy (e.g., Nginx, Cloudflare) and uses the `CF-Connecting-IP` header to identify the real client IP for rate limiting.
