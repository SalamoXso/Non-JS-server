import os
import secrets
import random
import string
import io
import base64
import logging
from flask import Flask, render_template, request, session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, validators
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, static_folder='static', template_folder=os.path.join(os.getcwd(), "templates"))
app.secret_key = secrets.token_urlsafe(32)  # Strong secret key
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

class VerificationForm(FlaskForm):
    field0 = StringField('Field 0', [validators.Length(min=1, max=1)])
    field1 = StringField('Field 1', [validators.Length(min=1, max=1)])
    field2 = StringField('Field 2', [validators.Length(min=1, max=1)])
    field3 = StringField('Field 3', [validators.Length(min=1, max=1)])
    field4 = StringField('Field 4', [validators.Length(min=1, max=1)])
    field5 = StringField('Field 5', [validators.Length(min=1, max=1)])

class ImageGenerator:
    def __init__(self, width=800, height=800):  # Increased dimensions for better visibility
        self.width = width
        self.height = height

        # List of font paths (replace with your own font paths)
        self.font_paths = [
            "arial.ttf",  # Default font (ensure this file exists)
            "times.ttf",  # Times New Roman (ensure this file exists)
            "cour.ttf",   # Courier New (ensure this file exists)
            "verdana.ttf",# Verdana (ensure this file exists)
            "comic.ttf",  # Comic Sans (ensure this file exists)
            "impact.ttf"  # Impact (ensure this file exists)
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

        # Choose a random font and set a larger font size.
        font_path = random.choice(self.font_paths)
        try:
            font = ImageFont.truetype(font_path, -200)  # Set font size to a larger value (200)
        except IOError:
            font = ImageFont.load_default()  # Fallback to default font if the chosen font fails

        # Calculate text position
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

        # Add a few random lines (light gray)
        for _ in range(5):  # Add 5 random lines
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line((x1, y1, x2, y2), fill=(180, 180, 180), width=1)  # Light gray lines

        # Add a few random dots (light gray)
        for _ in range(15):  # Add 15 random dots
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


def generate_random_char():
    return random.choice(string.ascii_letters + string.digits)


@app.route('/', methods=['GET', 'POST'])
@limiter.limit("20 per minute")  # Apply rate limiting to this route
def verification():
    form = VerificationForm()
    images = []
    success = None

    if form.validate_on_submit():
        logger.info(f"Form submitted by IP: {request.remote_addr}")
        
        user_input = [form.field0.data,
                      form.field1.data,
                      form.field2.data,
                      form.field3.data,
                      form.field4.data,
                      form.field5.data]
        
        correct_answers = session.get('correct_answers', [])
        
        logger.info(f"User input: {user_input}")
        logger.info(f"Correct answers: {correct_answers}")

        # Check if the user's input matches the correct answers
        if user_input == correct_answers:
            success = True
        else:
            success = False
            
            correct_answers = [generate_random_char() for _ in range(6)]
            session['correct_answers'] = correct_answers
            
            image_generator = ImageGenerator()
            images = [image_generator.generate_image(char) for char in correct_answers]
            
            logger.info(f"Generated images: {images}")

            # Clear the form fields on failure
            form.field0.data = ''
            form.field1.data = ''
            form.field2.data = ''
            form.field3.data = ''
            form.field4.data = ''
            form.field5.data = ''

    elif request.method == 'GET':
        correct_answers = [generate_random_char() for _ in range(6)]
        
        session['correct_answers'] = correct_answers
        
        image_generator = ImageGenerator()
        
        images = [image_generator.generate_image(char) for char in correct_answers]
        
        logger.info(f"Generated images on GET: {images}")

    return render_template('index.html', form=form, images=images, success=success)


if __name__ == '__main__':
    app.run(debug=True)
