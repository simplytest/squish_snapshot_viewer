import base64
import os

image_dir = "images"
for filename in os.listdir(image_dir):
    if filename.lower().endswith(".png"):
        path = os.path.join(image_dir, filename)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            data_url = f"data:image/png;base64,{b64}"
            out_path = os.path.join(image_dir, filename + ".base64.txt")
            with open(out_path, "w") as out_file:
                out_file.write(data_url)
        print(f"Erstellt: {out_path}")