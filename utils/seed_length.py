import cv2
import numpy as np
import pandas as pd
import os
import time

def process_seed(img_path, processed_image_folder, excel_folder):
    # Load the image
    image = cv2.imread(img_path)

    # Convert the image to grayscale for edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Detect edges using Canny Edge Detector
    edges = cv2.Canny(blurred, 30, 100)

    # Find contours from the edges
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Function to calculate the length of a contour's bounding box in millimeters
    def get_contour_length_mm(contour, pixels_per_mm):
        _, _, w, h = cv2.boundingRect(contour)
        return max(w, h) / pixels_per_mm  # Choose the longer side as the length

    # Define color range for detecting the blue reference circle
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([130, 255, 255])

    # Convert to HSV to detect colors
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create mask to detect blue color
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    blue_contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pixels_per_mm = None
    seed_lengths_mm = []

    # Find the largest contour in blue (assuming it's the reference circle)
    if blue_contours:
        largest_contour = max(blue_contours, key=cv2.contourArea)
        (x, y), radius = cv2.minEnclosingCircle(largest_contour)

        # Draw the detected reference circle in yellow
        cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 3)

        # Calculate pixels per millimeter using the reference circle's diameter
        reference_diameter_mm = 21  # Diameter of the reference circle in millimeters
        pixels_per_mm = (2 * radius) / reference_diameter_mm
    else:
        print("Blue reference circle not detected!")  # Optional logging

    # Proceed with seed detection only if the reference circle is detected
    if pixels_per_mm is not None:
        # Define color range for the seeds (adjust as necessary)
        lower_seed_color = np.array([160, 100, 100])
        upper_seed_color = np.array([180, 255, 255])

        # Create a mask for the seed color
        seed_mask = cv2.inRange(hsv, lower_seed_color, upper_seed_color)

        # Perform morphological operations to remove noise
        kernel = np.ones((5, 5), np.uint8)
        seed_mask_cleaned = cv2.morphologyEx(seed_mask, cv2.MORPH_OPEN, kernel)

        # Find contours of the seeds
        seed_contours, _ = cv2.findContours(seed_mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Loop over the seed contours and calculate their lengths
        valid_seed_id = 1
        for contour in seed_contours:
            length_mm = get_contour_length_mm(contour, pixels_per_mm)
            if length_mm > 1:  # Filter out very small noise
                seed_lengths_mm.append((valid_seed_id, length_mm))

                # Calculate centroid of the contour to position text
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                else:
                    cX, cY = 0, 0

                # Draw the contour and label the seed with ID and diameter
                cv2.drawContours(image, [contour], -1, (255, 255, 255), 2)
                cv2.putText(image, f"ID: {valid_seed_id}, {length_mm:.2f} mm", (cX - 50, cY - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                # Increment the valid seed counter
                valid_seed_id += 1

    else:
        print("No valid pixels per mm found. Exiting seed detection.")  # Optional logging

    # Generate unique filenames
    unique_id = str(int(time.time()))
    output_image_path = os.path.join(processed_image_folder, f"processed_image_{unique_id}.png")
    excel_path = os.path.join(excel_folder, f"seed_diameters_{unique_id}.xlsx")

    # Ensure directories exist before saving
    os.makedirs(processed_image_folder, exist_ok=True)
    os.makedirs(excel_folder, exist_ok=True)

    # Save the processed image and Excel file
    cv2.imwrite(output_image_path, image)
    df = pd.DataFrame(seed_lengths_mm, columns=["ID", "Diameter (mm)"])
    df.to_excel(excel_path, index=False)

    return output_image_path, excel_path
