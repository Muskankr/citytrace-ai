from PIL import Image, ImageDraw, ImageFont
import glob
import os
import math


files = sorted(
    glob.glob("outputs/pipeline_plates/track_*.jpg"),
    key=lambda x: int(
        os.path.basename(x).split("_")[1].split(".")[0]
    )
)

output_dir = "data/benchmark/sheets"
os.makedirs(output_dir, exist_ok=True)

font = ImageFont.truetype("arial.ttf", 28)

per_sheet = 8
cols = 2
cell_w = 800
cell_h = 300

for sheet_number in range(
    math.ceil(len(files) / per_sheet)
):

    batch = files[
        sheet_number * per_sheet:
        (sheet_number + 1) * per_sheet
    ]

    rows = math.ceil(len(batch) / cols)

    sheet = Image.new(
        "RGB",
        (cols * cell_w, rows * cell_h),
        "white"
    )

    draw = ImageDraw.Draw(sheet)

    for i, path in enumerate(batch):

        img = Image.open(path).convert("RGB")

        img.thumbnail((740, 220))

        x = (i % cols) * cell_w + 30
        y = (i // cols) * cell_h + 60

        filename = os.path.basename(path)

        draw.text(
            (x, y - 40),
            filename,
            fill="black",
            font=font
        )

        sheet.paste(img, (x, y))

    output = (
        f"{output_dir}/"
        f"batch_{sheet_number + 1}.jpg"
    )

    sheet.save(
        output,
        quality=95
    )

    print(f"Created: {output}")

print()
print(f"Total sheets: {math.ceil(len(files) / per_sheet)}")