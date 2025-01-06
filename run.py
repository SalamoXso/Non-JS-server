from flask import Flask, render_template, request, session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, validators
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import secrets
import random
import string
import io
import base64
import logging
from PIL import Image, ImageDraw, ImageFont

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')

# Set a strong secret key (use environment variable in production)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_urlsafe(32))

# Configure session settings for security
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access to cookies
    SESSION_COOKIE_SAMESITE='Lax'  # Prevent CSRF attacks
)

# Enable CSRF protection
csrf = CSRFProtect(app)

# Enable rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Limit by IP address
    default_limits=["20 per minute"]  # Allow 20 attempts per minute
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the verification form
class VerificationForm(FlaskForm):
    field0 = StringField('Field 0', [validators.Optional(), validators.Length(min=1, max=1)])
    field1 = StringField('Field 1', [validators.Optional(), validators.Length(min=1, max=1)])
    field2 = StringField('Field 2', [validators.Optional(), validators.Length(min=1, max=1)])
    field3 = StringField('Field 3', [validators.Optional(), validators.Length(min=1, max=1)])


# Image generator class
class ImageGenerator:
    def __init__(self, width=100, height=100):  # Increased dimensions for better visibility
        self.width = width
        self.height = height

        # List of font paths (relative to the project root)
        self.font_paths = [
            "fonts/Verdana.ttf",          # Verdana Regular
            "fonts/Verdana_Bold.ttf",     # Verdana Bold
            "fonts/Verdana_Italic.ttf",   # Verdana Italic
            "fonts/Courier_New.ttf",      # Courier New Regular
            "fonts/Arial.ttf",            # Arial Regular
            "fonts/Arial_Bold.ttf",       # Arial Bold
            "fonts/Arial_Italic.ttf",     # Arial Italic
            "fonts/Arial_Bold_Italic.ttf" # Arial Bold Italic
        ]

    def generate_image(self, text):
        # Create a blank image with a white background
        img = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(img)

        # Add a light background texture (e.g., a grid)
        for x in range(0, self.width, 10):
            draw.line((x, 0, x, self.height), fill=(220, 220, 220), width=1)  # Vertical lines
        for y in range(0, self.height, 10):
            draw.line((0, y, self.width, y), fill=(220, 220, 220), width=1)  # Horizontal lines

        # Choose a random font and set a large font size
        font_path = random.choice(self.font_paths)
        try:
            font_size = 0.1  # Set a large font size (adjust as needed)
            font = ImageFont.truetype(font_path, font_size*500)
        except IOError as e:
            logger.error(f"Failed to load font: {font_path}. Error: {e}")
            font = ImageFont.load_default()  # Fallback to default font if the chosen font fails

        # Calculate text position to center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((self.width - text_width) / 2, (self.height - text_height) / 2)

        # Draw the text with slight noise
        for dx in range(-1, 2):  # Add slight horizontal noise
            for dy in range(-1, 2):  # Add slight vertical noise
                if dx != 0 or dy != 0:  # Skip the original position
                    draw.text((position[0] + dx, position[1] + dy), text, font=font, fill=(200, 200, 200))  # Light gray noise
        
        draw.text(position, text, font=font, fill='black')  # Draw the main text

        # Add fewer random lines (light gray) with reduced thickness
        for _ in range(3):  # Reduced to 3 random lines
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line((x1, y1, x2, y2), fill=(180, 180, 180), width=1)  # Light gray lines with reduced thickness

        # Add fewer random dots (light gray)
        for _ in range(10):  # Reduced to 10 random dots
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=(180, 180, 180))  # Light gray dots

        # Save the image to an in-memory buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Encode the image as a base64 string
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{image_base64}"

# Helper function to generate random characters
def generate_random_char():
    return random.choice(string.ascii_letters + string.digits)

# Main route
@app.route('/', methods=['GET', 'POST'])
@limiter.limit("20 per minute")  # Apply rate limiting to this route
def verification():
    form = VerificationForm()
    images = []
    success = None
    current_field = session.get('current_field', 0)

    if request.method == 'GET':
        # Generate new unique correct answers and store them in the session
        correct_answers = [generate_random_char() for _ in range(4)]
        session['correct_answers'] = correct_answers
        
        # Generate new CAPTCHA images
        image_generator = ImageGenerator()
        images = [image_generator.generate_image(char) for char in correct_answers]
        
        logger.info(f"Generated images on GET: {images}")
        logger.info(f"Correct answers: {correct_answers}")

    elif form.validate_on_submit():
        logger.info(f"Form submitted by IP: {request.remote_addr}")
        
        # Get the correct answers from the session
        correct_answers = session.get('correct_answers', [])
        
        # Get the value of the current field from the form
        current_field_value = request.form.get(f'field{current_field}', '').strip().lower()
        correct_answer = correct_answers[current_field].strip().lower()
        
        logger.info(f"User input for field {current_field}: {current_field_value}")
        logger.info(f"Correct answer for field {current_field}: {correct_answer}")

        # Check if the user's input matches the correct answer for the current field
        if current_field_value == correct_answer:
            logger.info(f"Field {current_field} is correct.")
            current_field += 1
            session['current_field'] = current_field
            if current_field >= 4:
                success = True
                session.pop('current_field', None)
                session.pop('correct_answers', None)
                logger.info("All fields are correct. Verification successful.")
        else:
            logger.info(f"Field {current_field} is incorrect.")
            success = False
            current_field = 0
            session['current_field'] = current_field
            
            # Generate new unique correct answers and store them in the session
            correct_answers = [generate_random_char() for _ in range(4)]
            session['correct_answers'] = correct_answers
            
            # Generate new CAPTCHA images
            image_generator = ImageGenerator()
            images = [image_generator.generate_image(char) for char in correct_answers]
            
            logger.info(f"Generated new images: {images}")
            logger.info(f"New correct answers: {correct_answers}")

            # Clear the form fields on failure
            form.field0.data = ''
            form.field1.data = ''
            form.field2.data = ''
            form.field3.data = ''
            
    else:
        # Log form validation errors
        logger.info(f"Form validation failed. Errors: {form.errors}")

    # If the form is not submitted or validation fails, use the existing session data
    if not images:
        correct_answers = session.get('correct_answers', [])
        image_generator = ImageGenerator()
        images = [image_generator.generate_image(char) for char in correct_answers]

    return render_template('index.html', form=form, images=images, success=success, current_field=current_field)
# Run the app
if __name__ == '__main__':
    app.run(debug=True)
