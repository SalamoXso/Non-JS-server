import os
import secrets
from flask import Flask, render_template, request, jsonify, session, current_app, url_for
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, static_folder='static', template_folder=os.path.join(os.getcwd(), "app", "templates"))

app.secret_key = secrets.token_urlsafe(16)  # Secret key for session management

class ImageGenerator:
    def __init__(self, width=200, height=100):
        self.width = width
        self.height = height
        
        # Try using default font if arial.ttf is unavailable
        try:
            self.font = ImageFont.truetype("arial.ttf", 30)
        except IOError:
            print("Arial font not found, using default font.")
            self.font = ImageFont.load_default()

    def generate_image(self, text):
        # Create a new image with a white background
        img = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(img)

        # Add text to the image
        draw.text((10, 10), text=text, font=self.font, fill='black')

        # Generate a random filename
        random_str = secrets.token_urlsafe(16)  # Generate a secure token-based filename
        filename = f"{random_str}.png"
        
        # Define the save path using Flask's current_app
        save_dir = os.path.join(current_app.root_path, 'static', 'images', 'generated_images')
        print(f"Saving image to: {save_dir}")  # Debugging statement

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)  # Create the directory if it doesn't exist

        image_path = os.path.join(save_dir, filename)
        print(f"Generated image path: {image_path}")  # Debugging statement

        try:
            img.save(image_path)  # Save the image
            print(f"Image saved at: {image_path}")  # Debugging statement
        except Exception as e:
            print(f"Error saving image: {e}")  # Error handling

        return filename


def verify(user_input):
    # Implement your verification logic here
    if all(field.strip() != "" for field in user_input):  # Check that no fields are empty
        return True
    else:
        return False


@app.route('/', methods=['GET', 'POST'])
def verification():
    images = []  # Initialize an empty list to hold image filenames

    if request.method == 'POST':
        # Handle form submission
        user_input = [request.form.get(f'field{i}') for i in range(6)]  # Get the values for fields

        # Initialize the image generator
        generator = ImageGenerator()

        # Generate images based on inputs
        for i in range(6):
            if user_input[i]:  # Check if the input field is not empty
                print(f"Generating image for field{i}: {user_input[i]}")  # Debugging statement
                image_filename = generator.generate_image(user_input[i])  # Generate image
                if image_filename:
                    images.append(image_filename)  # Add the filename to the list
                else:
                    print(f"Image generation failed for input: {user_input[i]}")  # Debugging statement

        # Implement your verification logic
        success = verify(user_input)  # Call the verify function

        return render_template('verification.html', images=images, success=success)

    return render_template('verification.html', images=images)


if __name__ == '__main__':
    app.run(debug=True)
