from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import os
from utils.image_processing import process_image
from utils.moisture_calculation import calculate_remaining_moisture
from utils.excel_handler import update_excel
from utils.seed_length import process_seed  # Importing seed length estimator
from flask_bcrypt import Bcrypt
import pandas as pd

app = Flask(__name__)
app.secret_key = 'abfa85c7b8d5f49fbc7e5d04ac862071'  # Replace with your own secret key
bcrypt = Bcrypt(app)

# In-memory user storage (for testing)
users_db = {
    'user1': bcrypt.generate_password_hash('user@123').decode('utf-8'),
    'user2': bcrypt.generate_password_hash('userpass').decode('utf-8')
}

# Verify user credentials (no database)
def verify_user(username, password):
    if username in users_db:
        return bcrypt.check_password_hash(users_db[username], password)
    return False

# Upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if verify_user(username, password):
            session['username'] = username  # Store the username in session
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to the main page after login
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))  # Redirect to login page

# Route for the main page (requires login)
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    if request.method == 'POST':
        # Check which action was requested
        if 'red_chili_analyzer' in request.form:
            return redirect(url_for('red_chili_analyzer'))
        elif 'data_visualization' in request.form:
            return redirect(url_for('data_visualization'))
        elif 'seed_length_estimator' in request.form:
            return redirect(url_for('seed_length_estimator'))

    return render_template('index.html')

@app.route('/red_chili_analyzer', methods=['GET', 'POST'])
def red_chili_analyzer():
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        print("POST request received")
        file = request.files.get('image')  # Using .get() for safe access
        weight = request.form.get('weight')  # Using .get() for safe access
        print(f"File: {file}, Weight: {weight}")

        if not file:
            print('Please upload an image file.', 'danger')
            return redirect(url_for('red_chili_analyzer'))  # Redirecting back for the user to upload again

        if not weight:
            print('Please enter the weight.', 'danger')
            return redirect(url_for('red_chili_analyzer'))  # Redirecting back for the user to input weight

        if not allowed_file(file.filename):
            print('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF image.', 'danger')
            return redirect(url_for('red_chili_analyzer'))  # Redirecting back for the user to upload a valid file

        try:
            # Save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Process the image to extract features
            features = process_image(file_path)

            # Calculate moisture content
            W_initial = 1020  # Starting weight (initial weight of chilies)
            W_current = float(weight)
            remaining_moisture = calculate_remaining_moisture(W_initial, W_current)

            # Calculate moisture loss percentage
            moisture_loss_percentage = ((W_initial - W_current) / W_initial) * 100

            # Update Excel with results
            update_excel(features, remaining_moisture, W_current)

            # Render red_chili_analyzer.html with results and the uploaded image filename
            return render_template('red_chili_analyzer.html', 
                                   features=features, 
                                   weight=W_current, 
                                   moisture=remaining_moisture, 
                                   moisture_loss=moisture_loss_percentage, 
                                   filename=filename)

        except Exception as e:
            flash(f"An error occurred while processing the image: {e}", 'danger')
            return redirect(url_for('red_chili_analyzer'))  # Redirect back to handle the error

    # If the request is GET, render the form
    return render_template('red_chili_analyzer.html')

# New route for seed length estimator
@app.route('/chilli', methods=['GET', 'POST'])
def chilli():
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('image')

        if not file:
            flash('Please upload an image file.', 'danger')
            return redirect(url_for('chilli'))

        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF image.', 'danger')
            return redirect(url_for('chilli'))

        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Process the image and get paths for the processed image and Excel file
            processed_image_folder = 'static/processed_images'
            excel_folder = 'static/excel_files'
            os.makedirs(processed_image_folder, exist_ok=True)
            os.makedirs(excel_folder, exist_ok=True)

            processed_image_path, excel_path = process_seed(file_path, processed_image_folder, excel_folder)

            # Render the template with processed image and Excel file paths
            return render_template(
                'chilli.html', 
                processed_image_path=processed_image_path,
                excel_path=excel_path,
                filename=filename
            )

        except Exception as e:
            flash(f"An error occurred while processing the image: {e}", 'danger')
            return redirect(url_for('chilli'))

    return render_template('chilli.html')


@app.route('/data-visualization')
def data_visualization():
    try:
        df = pd.read_excel('data/chili_data.xlsx')
    except FileNotFoundError:
        return "Excel file not found!", 404

    data = {
        'dates': df['Date'].tolist(),
        'weights': df['Weight(g)'].tolist(),
        'moisture_loss': df['Moisture loss Content (%)'].tolist(),
        'mean_hue': df['Mean Hue'].tolist(),
        'mean_saturation': df['Mean Saturation'].tolist(),
        'mean_value': df['Mean Value'].tolist(),
        'contrast': df['Contrast'].tolist(),
        'correlation': df['Correlation'].tolist(),
        'entropy': df['Entropy'].tolist()
    }
    return render_template('data_visualization.html', data=data)

@app.route('/download_excel')
def download_excel():
    file_path = 'data/chili_data.xlsx'
    if os.path.exists(file_path):
        return send_from_directory(directory=os.path.dirname(file_path),
                                   path=os.path.basename(file_path),
                                   as_attachment=True)
    else:
        flash('Excel file not found.', 'danger')
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
