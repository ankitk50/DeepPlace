#!/usr/bin/env python3
"""
Script to generate 100 PNG images with colored boxes using tkinter.
Each image contains boxes in red, green, blue, orange, and yellow with different sizes.
"""

import os
import random
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw

# Colors: red, green, blue, orange, yellow
COLORS = {
    'red': '#FF0000',
    'green': '#00FF00',
    'blue': '#0000FF',
    'orange': '#FFA500',
    'yellow': '#FFFF00'
}

# Image dimensions
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600


def generate_image_with_tkinter(image_number, output_dir):
    """
    Generate a single image with 5 colored boxes using tkinter Canvas.
    
    Args:
        image_number: The image number (for filename)
        output_dir: Directory to save the image
    """
    # Create a hidden tkinter window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create a canvas
    canvas = tk.Canvas(root, width=IMAGE_WIDTH, height=IMAGE_HEIGHT, bg='white')
    canvas.pack()
    
    # Generate 5 boxes with different sizes
    color_list = list(COLORS.keys())
    
    for color_name in color_list:
        # Random box size (between 50x50 and 200x200)
        box_width = random.randint(50, 200)
        box_height = random.randint(50, 200)
        
        # Random position (ensuring box fits within image)
        x = random.randint(0, IMAGE_WIDTH - box_width)
        y = random.randint(0, IMAGE_HEIGHT - box_height)
        
        # Draw rectangle on canvas
        canvas.create_rectangle(
            x, y, x + box_width, y + box_height,
            fill=COLORS[color_name],
            outline='black',
            width=2
        )
    
    # Save canvas as PNG using postscript conversion
    filename = f"image_{image_number:03d}.png"
    filepath = output_dir / filename
    
    # Export canvas to postscript, then convert to PNG
    canvas.postscript(file=str(filepath).replace('.png', '.eps'), colormode='color')
    
    # Convert EPS to PNG using PIL
    img = Image.open(str(filepath).replace('.png', '.eps'))
    img.save(filepath, 'PNG')
    
    # Clean up EPS file
    eps_file = filepath.with_suffix('.eps')
    if eps_file.exists():
        eps_file.unlink()
    
    root.destroy()
    return filepath


def generate_image_pil(image_number, output_dir):
    """
    Generate a single image with 5 colored boxes using PIL (more reliable).
    This is the recommended method.
    
    Args:
        image_number: The image number (for filename)
        output_dir: Directory to save the image
    """
    # Create a new image with white background
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color='white')
    draw = ImageDraw.Draw(img)
    
    # Color mapping for PIL (RGB tuples)
    color_map = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'orange': (255, 165, 0),
        'yellow': (255, 255, 0)
    }
    
    # Generate 5 boxes with different sizes
    color_list = list(COLORS.keys())
    
    for color_name in color_list:
        # Random box size (between 50x50 and 200x200)
        box_width = random.randint(50, 200)
        box_height = random.randint(50, 200)
        
        # Random position (ensuring box fits within image)
        x = random.randint(0, IMAGE_WIDTH - box_width)
        y = random.randint(0, IMAGE_HEIGHT - box_height)
        
        # Draw rectangle
        draw.rectangle(
            [x, y, x + box_width, y + box_height],
            fill=color_map[color_name],
            outline='black',
            width=2
        )
    
    # Save the image
    filename = f"image_{image_number:03d}.png"
    filepath = output_dir / filename
    img.save(filepath, 'PNG')
    
    return filepath


def main():
    """Generate 100 PNG images with colored boxes."""
    # Create output directory
    script_dir = Path(__file__).parent
    images_dir = script_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    print(f"Generating 100 images in: {images_dir}")
    print("Each image will contain 5 boxes (red, green, blue, orange, yellow) with different sizes...")
    print("Using PIL method (more reliable than tkinter for image generation)...")
    
    # Generate 100 images
    # Note: Using PIL method as it's more reliable for batch generation
    # Tkinter method is available but slower and requires GUI backend
    for i in range(1, 101):
        filepath = generate_image_pil(i, images_dir)
        if i % 10 == 0:
            print(f"Generated {i}/100 images...")
    
    print(f"\n✓ Successfully generated 100 PNG files in: {images_dir}")
    print(f"  Files: image_001.png through image_100.png")


if __name__ == '__main__':
    main()

