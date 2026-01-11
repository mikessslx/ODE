import fitz # PyMuPDF
import re
import sys
import os
from PIL import Image

"""
Images processor

Usage:
    python images.py [filename.pdf]

Dependencies:
    pip install pymupdf Pillow
"""

def stitch_images(folder_path, group_size=2):
    valid_exts = ('.png', '.jpg', '.jpeg', '.bmp')

    files = [f for f in os.listdir(folder_path) 
             if f.lower().endswith(valid_exts) and not f.startswith("combined")]
    
    if not files: return
    files.sort() # Ensure correct order

    # Split into groups
    for group_idx in range(0, len(files), group_size):
        group_files = files[group_idx:group_idx + group_size]
        try:
            images = [Image.open(os.path.join(folder_path, f)) for f in group_files]
            
            # Align to max width
            max_width = max(img.width for img in images)
            total_height = 0
            resized_images = []
            
            for img in images:
                if img.width != max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                resized_images.append(img)
                total_height += img.height

            # Create canvas
            canvas = Image.new('RGB', (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in resized_images:
                canvas.paste(img, (0, y_offset))
                y_offset += img.height
                
            save_path = os.path.join(folder_path, f"combined_{group_idx//group_size + 1:03d}.png")
            canvas.save(save_path)
            print(f"  + Stitched -> {save_path}")
            
        except Exception as e:
            print(f"  ! Stitching failed: {e}")

def extract_images(pdf_path, output_dir="images"):
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found!")
        return

    print(f"Processing: {pdf_path}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    events = [] # Stores (sort_key, type, value, page_idx, y)
    date_pattern = re.compile(r'^\d{1,2}[\./]\d{1,2}$') # Matches 12.12, 12/12

    # 1. Scan Document
    for i in range(len(doc)):
        page = doc.load_page(i)
        left_margin_limit = page.rect.width * 0.18
        
        # Find dates
        for w in page.get_text("words"):
            x0, y0, x1, y1, text, *rest = w
            if x1 <= left_margin_limit and date_pattern.match(text):
                events.append({
                    'sort_key': (i, y0),
                    'type': 'date',
                    'value': text,
                    'page_idx': i
                })

        # Find images
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            for img_rect in page.get_image_rects(xref):
                if img_rect.width < 50 or img_rect.height < 50: continue # Skip icons
                
                events.append({
                    'sort_key': (i, img_rect.y0),
                    'type': 'image',
                    'xref': xref,
                    'ext': img_info[8],
                    'page_idx': i
                })

    events.sort(key=lambda x: x['sort_key'])

    # 2. Extract & Save
    current_date = "Uncategorized"
    current_dir = None
    count = 0
    total = 0
    
    for e in events:
        if e['type'] == 'date':
            clean_date = e['value'].replace('/', '.')
            if clean_date != current_date:
                if current_dir: stitch_images(current_dir)
                current_date = clean_date
                current_dir = None
                count = 0
                print(f"> Date: {current_date}")

        elif e['type'] == 'image':
            date_dir = os.path.join(output_dir, current_date)
            os.makedirs(date_dir, exist_ok=True)
            current_dir = date_dir
            
            count += 1
            total += 1
            
            try:
                # Extraction
                img_data = doc.extract_image(e['xref'])
                if img_data:
                    ext = img_data["ext"]
                    data = img_data["image"]
                    fname = f"img_{count:03d}_p{e['page_idx']+1}.{ext}"
                    with open(os.path.join(date_dir, fname), "wb") as f: f.write(data)
                else:
                    pix = fitz.Pixmap(doc, e['xref'])
                    if pix.n - pix.alpha > 3: pix = fitz.Pixmap(fitz.csRGB, pix)
                    fname = f"img_{count:03d}_p{e['page_idx']+1}.png"
                    pix.save(os.path.join(date_dir, fname))
                    pix = None
                
                print(f"  + Saved: {current_date}/{fname}")
                
            except Exception as err:
                print(f"  ! Error saving image: {err}")
    
    if current_dir: stitch_images(current_dir)

    print(f"\nDone! {total} images saved to {output_dir}")
    doc.close()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "111.pdf"
    output_folder = os.path.splitext(target)[0] + "_images"
    extract_images(target, output_folder)
