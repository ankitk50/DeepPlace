import cv2
import numpy as np
import csv
import glob

def load_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot load image: {image_path}")
    return img

def preprocess_edges(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    return edges

def find_quadrilateral_rectangles(edges, total_pixels, area_min=500, area_max_ratio=0.8):
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rect_bboxes = []
    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            area = w * h
            if area < area_min or area > (total_pixels * area_max_ratio):
                continue
            rect_bboxes.append((x, y, w, h))
    return rect_bboxes

def dominant_color_rgb(roi_bgr):
    pixels = roi_bgr.reshape(-1, 3).astype(np.float32)
    _, _, centers = cv2.kmeans(
        pixels,
        1,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
        10,
        cv2.KMEANS_RANDOM_CENTERS,
    )
    dominant_bgr = centers[0].astype(int).flatten()
    return tuple(dominant_bgr[::-1])  # RGB

def annotate_and_collect(img, original, bboxes, total_pixels):
    height, width = img.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    rectangles = []
    print(f"{'ID':<4} {'Area (px²)':<12} {'Width':<8} {'Height':<8} {'Color (RGB)':<15} {'% of Image'}")
    print("-" * 75)
    for i, (x, y, w, h) in enumerate(bboxes, start=1):
        area = w * h
        roi = original[y:y+h, x:x+w]
        color_rgb = dominant_color_rgb(roi)
        rectangles.append({
            'id': i,
            'area': area,
            'width': w,
            'height': h,
            'color_rgb': color_rgb,
            'bbox': (x, y, w, h)
        })
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        percent = (area / total_pixels) * 100
        print(f"{i:<4} {area:<12} {w:<8} {h:<8} {str(color_rgb):<15} {percent:.2f}%")
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(img, str(i), (x + 5, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    return rectangles, mask

def calculate_bounding_box_of_all_rectangles(rectangles):
    """Calculate the bounding box that contains all detected rectangles."""
    if not rectangles:
        return None
    
    min_x = min(r['bbox'][0] for r in rectangles)
    min_y = min(r['bbox'][1] for r in rectangles)
    max_x = max(r['bbox'][0] + r['bbox'][2] for r in rectangles)
    max_y = max(r['bbox'][1] + r['bbox'][3] for r in rectangles)
    
    return (min_x, min_y, max_x - min_x, max_y - min_y)

def summarize_and_label(img, mask, rectangles, total_pixels):
    height, width = img.shape[:2]
    real_occupied_pixels = int(np.sum(mask == 255))
    
    # Calculate gaps only within the bounding box of all rectangles
    bbox = calculate_bounding_box_of_all_rectangles(rectangles)
    if bbox:
        x, y, w, h = bbox
        # Create a mask of only the region containing rectangles
        roi_mask = mask[y:y+h, x:x+w]
        content_area_pixels = w * h
        occupied_in_content = int(np.sum(roi_mask == 255))
        gap_pixels = content_area_pixels - occupied_in_content
        gap_percentage = (gap_pixels / content_area_pixels) * 100 if content_area_pixels > 0 else 0
    else:
        content_area_pixels = 0
        gap_pixels = 0
        gap_percentage = 0
    
    # Old calculation (including borders/padding)
    empty_pixels = total_pixels - real_occupied_pixels
    empty_percentage = (empty_pixels / total_pixels) * 100
    
    print("=" * 75)
    print(f"Image resolution          : {width} × {height} = {total_pixels:,} pixels")
    print(f"Detected rectangles       : {len(rectangles)}")
    print(f"Pixels covered (no overlap): {real_occupied_pixels:,}")
    if bbox:
        print(f"Content area (bbox)       : {content_area_pixels:,} pixels")
        print(f"Gap pixels (excl borders) : {gap_pixels:,}")
        print(f"Gap percentage (excl borders): {gap_percentage:.2f}%")
    print(f"Total empty pixels (incl borders): {empty_pixels:,}")
    print(f"Total empty percentage    : {empty_percentage:.2f}%")
    print(f"Filled percentage         : {100 - empty_percentage:.2f}%")
    
    # Update label to show gap without borders
    if bbox:
        cv2.putText(img, f"Gaps: {gap_pixels:,} px ({gap_percentage:.1f}%)",
                    (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    else:
        cv2.putText(img, f"Empty: {empty_pixels:,} px ({empty_percentage:.1f}%)",
                    (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    
    return {
        'total_pixels': total_pixels,
        'occupied_pixels': real_occupied_pixels,
        'content_area_pixels': content_area_pixels,
        'gap_pixels': gap_pixels,
        'gap_percentage': gap_percentage,
        'empty_pixels': empty_pixels,
        'empty_percentage': empty_percentage,
        'rectangle_count': len(rectangles),
        'rectangles': rectangles,
        'content_bbox': bbox
    }

def save_outputs(image_path, img, mask, rectangles, total_pixels):
    image_name = image_path.split("/")[-1].split(".")[0]
    cv2.imwrite(f"output/{image_name}_rectangles_labeled.jpg", img)
    cv2.imwrite(f"output/{image_name}_mask_occupied_areas.jpg", mask)
    with open(f"output/{image_name}_rectangle_report.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Area_px", "Width", "Height", "Color_RGB", "Percentage"])
        for r in rectangles:
            writer.writerow([r['id'], r['area'], r['width'], r['height'], r['color_rgb'],
                             (r['area']/total_pixels)*100])
    print("\nFiles saved:")
    print("   → output/output_rectangles_labeled.jpg")
    print("   → output/mask_occupied_areas.jpg")
    print("   → output/rectangle_report.csv")

def analyze_rectangles_and_empty_space(image_path):
    img = load_image(image_path)
    original = img.copy()
    height, width = img.shape[:2]
    total_pixels = width * height
    edges = preprocess_edges(img)
    bboxes = find_quadrilateral_rectangles(edges, total_pixels)
    rectangles, mask = annotate_and_collect(img, original, bboxes, total_pixels)
    summary = summarize_and_label(img, mask, rectangles, total_pixels)
    save_outputs(image_path, img, mask, rectangles, total_pixels)
    return summary

# ==================== RUN IT ====================
if __name__ == "__main__":
    image_paths = glob.glob("data/*.png")   # ← Change to your image!
    for image_path in sorted(image_paths):
        print(f"\nAnalyzing image: {image_path}\n")
        result = analyze_rectangles_and_empty_space(image_path)