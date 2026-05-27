import os
from PIL import Image

src_image_path = r"C:\Users\mjddw\.gemini\antigravity\brain\b7d5650e-ab16-4b57-bc70-8ed6abba07a0\app_icon_1779869245564.png"
assets_dir = r"c:\Users\mjddw\Desktop\DSG_JAVA\Yxad_Engine_PlugIn_For_AVRO\KindleFly\assets"

os.makedirs(assets_dir, exist_ok=True)

try:
    img = Image.open(src_image_path)
    
    # Save standard PNG icon (e.g., 256x256)
    png_path = os.path.join(assets_dir, "app_icon.png")
    img_resized = img.resize((256, 256), Image.Resampling.LANCZOS)
    img_resized.save(png_path, "PNG")
    print(f"Saved PNG to {png_path}")
    
    # Save standard Windows ICO icon (contains multiple sizes for Windows explorer)
    ico_path = os.path.join(assets_dir, "app_icon.ico")
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Saved ICO to {ico_path}")
    
except Exception as e:
    print(f"Error processing image: {e}")
