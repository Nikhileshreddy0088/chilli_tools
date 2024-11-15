import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops


def segment_chilies(image):
    """Segment the chilies from the background using refined color thresholding and contour filtering."""
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define a refined range for red color to capture chili characteristics
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    # Create two masks to capture both ends of the red spectrum
    red_mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    
    # Refine the mask using morphological operations
    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    red_mask = cv2.dilate(red_mask, kernel, iterations=1)
    
    # Extract contours and filter based on area to focus only on larger chili-shaped areas
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_filtered = np.zeros_like(red_mask)
    
    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Adjust the area threshold based on chili size in the image
            cv2.drawContours(mask_filtered, [contour], -1, 255, thickness=cv2.FILLED)
    
    # Apply the filtered mask to the original image to get only the chili areas
    chilies_segmented = cv2.bitwise_and(image, image, mask=mask_filtered)
    
    return chilies_segmented, mask_filtered


def process_image(image_path):
    image = cv2.imread(image_path)
    
    # Segment chili from the background
    segmented_image, chili_mask = segment_chilies(image)
    
    # Extract color features
    mean_hue, mean_saturation, mean_value = calculate_hsv_means(segmented_image)
    
    # Extract texture features
    gray_image = cv2.cvtColor(segmented_image, cv2.COLOR_BGR2GRAY)
    contrast, correlation, entropy = calculate_texture_features(gray_image)
    
    # Extract shape and size features
    area, perimeter, aspect_ratio = calculate_shape_size(segmented_image)
    
    features = {
        'mean_hue': mean_hue,
        'mean_saturation': mean_saturation,
        'mean_value': mean_value,
        'contrast': contrast,
        'correlation': correlation,
        'entropy': entropy
    }
    
    return features

def calculate_hsv_means(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mean_hue = np.mean(hsv_image[:, :, 0])
    mean_saturation = np.mean(hsv_image[:, :, 1])
    mean_value = np.mean(hsv_image[:, :, 2])
    return mean_hue, mean_saturation, mean_value

def calculate_texture_features(gray_image):
    glcm = graycomatrix(gray_image, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
    contrast = graycoprops(glcm, 'contrast')[0, 0]
    correlation = graycoprops(glcm, 'correlation')[0, 0]
    entropy = -np.sum(glcm * np.log2(glcm + np.finfo(float).eps))
    return contrast, correlation, entropy

def calculate_shape_size(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, threshold_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(threshold_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Assuming one chili, get the largest contour
    chili_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(chili_contour)
    perimeter = cv2.arcLength(chili_contour, True)
    aspect_ratio = float(cv2.boundingRect(chili_contour)[2]) / cv2.boundingRect(chili_contour)[3]
    
    return area, perimeter, aspect_ratio


def calculate_shape_size(image):
    """Calculate shape and size descriptors such as area, perimeter, and aspect ratio."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        return area, perimeter, aspect_ratio
    else:
        return None, None, None
