"""
Utility functions for data extraction.
"""

async def normalize_ocr(result, img_width, img_height):
    annotations = []

    if not result.read or not result.read.blocks:
        return annotations

    for block in result.read.blocks:
        for line in block.lines:
            text = " ".join(word.text for word in line.words)

            xs, ys = [], []
            for word in line.words:
                for p in word.bounding_polygon:
                    xs.append(p.x)
                    ys.append(p.y)

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            annotations.append({
                "text": text,
                "left": x_min / img_width,
                "top": y_min / img_height,
                "width": (x_max - x_min) / img_width,
                "height": (y_max - y_min) / img_height,
            })

    return annotations