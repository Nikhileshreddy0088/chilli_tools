import pandas as pd
from datetime import datetime

def update_excel(features, remaining_moisture, W_current, ):
    # Load the existing Excel file or create a new one if it doesn't exist
    file_path = 'data/chili_data.xlsx'
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        # Create a new DataFrame if the file doesn't exist
        df = pd.DataFrame(columns=[
            'Date', 'Time', 'Weight(g)', 'Moisture loss Content (%)',  
            'Mean Hue', 'Mean Saturation', 'Mean Value', 'Contrast', 
            'Correlation', 'Entropy'
        ])
    
    # Get the current date and time
    date_today = datetime.now().strftime('%d-%m-%Y')
    time_now = datetime.now().strftime('%H:%M:%S')
    # Prepare data for the new row
    new_data = pd.DataFrame({
        'Date': [date_today],
        'Time': [time_now],
        'Weight(g)': [W_current],
        'Moisture loss Content (%)': [remaining_moisture],
        'Mean Hue': [features['mean_hue']],
        'Mean Saturation': [features['mean_saturation']],
        'Mean Value': [features['mean_value']],
        'Contrast': [features['contrast']],
        'Correlation': [features['correlation']],
        'Entropy': [features['entropy']]
    })
    # Concatenate the new data with the existing DataFrame
    df = pd.concat([df, new_data], ignore_index=True)
    # Write the updated DataFrame back to the Excel file
    df.to_excel(file_path, index=False)
