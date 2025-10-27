"""Simple icon generator"""

from PIL import Image, ImageDraw, ImageFont

# Create 256x256 icon
img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw background circle
draw.ellipse([20, 20, 236, 236], fill='#007acc', outline='#005a9e', width=4)

# Draw "ADB" text
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()

draw.text((128, 128), "ADB", fill='white', font=font, anchor='mm')

# Save as ICO
img.save('resources/icon.ico', format='ICO')
print("Icon created: resources/icon.ico")
