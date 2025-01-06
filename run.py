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
app.secret_key = secrets.token_urlsafe(32)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

csrf = CSRFProtect(app)
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["20 per minute"])
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
    def __init__(self, width=200, height=200):  # Increased image size to 200x200
        self.width = width
        self.height = height
        self.font_paths = ["arial.ttf", "times.ttf", "cour.ttf", "verdana.ttf", "comic.ttf", "impact.ttf"]

    def generate_image(self, text):
        img = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(img)

        # Background texture
        for x in range(0, self.width, 10):
            draw.line((x, 0, x, self.height), fill=(220, 220, 220), width=1)
        for y in range(0, self.height, 10):
            draw.line((0, y, self.width, y), fill=(220, 220, 220), width=1)

        font_path = random.choice(self.font_paths)
        try:
            font_size = 200  # Start with a very large font size
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()

        # Reduce size if text is too big
        min_font_size = 40  # Ensure a minimum readable size
        while True:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            if text_width <= self.width * 0.8 and text_height <= self.height * 0.8:
                break  # Stop shrinking when text fits inside the image
            font_size -= 5  # Reduce font size step by step
            if font_size < min_font_size:
                font_size = min_font_size
                break  # Don't shrink below this size
            font = ImageFont.truetype(font_path, font_size)

        # Center the text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((self.width - text_width) // 2, (self.height - text_height) // 2)

        # Draw text with light noise
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx != 0 or dy != 0:
                    draw.text((position[0] + dx, position[1] + dy), text, font=font, fill=(200, 200, 200))
        draw.text(position, text, font=font, fill='black')

        # Add noise
        for _ in range(5):
            x1, y1, x2, y2 = random.randint(0, self.width), random.randint(0, self.height), random.randint(0, self.width), random.randint(0, self.height)
            draw.line((x1, y1, x2, y2), fill=(180, 180, 180), width=1)

        for _ in range(15):
            draw.point((random.randint(0, self.width), random.randint(0, self.height)), fill=(180, 180, 180))

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

def generate_random_char():
    return random.choice(string.ascii_letters + string.digits)

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def verification():
    form = VerificationForm()
    images = []
    success = None

    if form.validate_on_submit():
        logger.info(f"Form submitted by IP: {request.remote_addr}")
        user_input = [form.field0.data, form.field1.data, form.field2.data, form.field3.data, form.field4.data, form.field5.data]
        correct_answers = session.get('correct_answers', [])
        logger.info(f"User input: {user_input}")
        logger.info(f"Correct answers: {correct_answers}")

        if user_input == correct_answers:
            success = True
        else:
            success = False
            correct_answers = [generate_random_char() for _ in range(6)]
            session['correct_answers'] = correct_answers
            image_generator = ImageGenerator()
            images = [image_generator.generate_image(char) for char in correct_answers]

            for field in form:
                field.data = ''

    elif request.method == 'GET':
        correct_answers = [generate_random_char() for _ in range(6)]
        session['correct_answers'] = correct_answers
        image_generator = ImageGenerator()
        images = [image_generator.generate_image(char) for char in correct_answers]

    return render_template('index.html', form=form, images=images, success=success)

if __name__ == '__main__':
    app.run(debug=True)
