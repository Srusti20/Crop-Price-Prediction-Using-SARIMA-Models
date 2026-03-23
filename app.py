import smtplib
import traceback
from email.message import EmailMessage
from flask import Flask, render_template, jsonify, request, send_file, session, redirect
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import datetime
import os
import base64
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import io
import json
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = 'vewfhVLAjFEBHF'  # Can be any random string

# Base directory for datasets and crop suggestions JSON
DATASET_DIR = "templates"

# Email Config (using Gmail SMTP)
EMAIL_ADDRESS = "sanchitaharish2005@gmail.com"
EMAIL_PASSWORD = "ulgyyssjycoxuefa"


class TimeSeriesPreprocessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None

    def load_data(self):
        """Loads and validates the dataset."""
        self.data = pd.read_csv(self.file_path)
        required_columns = ['Price Date', 'Modal Price (Rs./Quintal)']
        for col in required_columns:
            if col not in self.data.columns:
                raise ValueError(f"Missing required column: {col}")

    def preprocess_data(self):
        """Preprocesses data for SARIMA model."""
        # Convert date and price columns
        self.data['Price Date'] = pd.to_datetime(self.data['Price Date'], errors='coerce')
        self.data['Modal Price (Rs./Quintal)'] = pd.to_numeric(self.data['Modal Price (Rs./Quintal)'], errors='coerce')

        # Drop rows with missing values in critical columns
        self.data.dropna(subset=['Price Date', 'Modal Price (Rs./Quintal)'], inplace=True)

        # Group by month and calculate the average modal price per month
        self.data['Month'] = self.data['Price Date'].dt.to_period('M')
        monthly_data = self.data.groupby('Month')['Modal Price (Rs./Quintal)'].mean()

        # Fill missing values with the last valid observation
        monthly_data = monthly_data.fillna(method='ffill')

        return monthly_data


class SARIMAModel:
    def __init__(self, time_series_data):
        self.time_series_data = time_series_data
        self.model = None
        self.model_fit = None

    def fit_model(self):
        """Fits a SARIMA model to the time series data."""
        try:
            self.model = SARIMAX(self.time_series_data,
                                 order=(2, 1, 2),
                                 seasonal_order=(1, 1, 1, 6),
                                 enforce_stationarity=False,
                                 enforce_invertibility=False)

            self.model_fit = self.model.fit(disp=False)
            print("Model fitted successfully.")
        except Exception as e:
            print(f"Error while fitting the model: {e}")

    def forecast(self, steps=6):
        """Generates future price predictions."""
        try:
            forecast = self.model_fit.get_forecast(steps=steps)
            
            # Use to_timestamp() to convert period index to datetime
            forecast_index = pd.date_range(start=self.time_series_data.index[-1].to_timestamp(), 
                                           periods=steps + 1, freq='ME')[1:]
            forecast_values = forecast.predicted_mean
            return forecast_index, forecast_values
        except Exception as e:
            print(f"Error while forecasting: {e}")
            return pd.Series(dtype=float), pd.Series(dtype=float)


def forecast_range(model_obj, start_date: str, end_date: str):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    last_known_date = model_obj.time_series_data.index[-1].to_timestamp()
    months_to_forecast = (end_date.year - last_known_date.year) * 12 + (end_date.month - last_known_date.month)

    if months_to_forecast <= 0:
        raise ValueError("End date must be after the last date in the dataset.")

    forecast_index, forecast_values = model_obj.forecast(steps=months_to_forecast)
    forecast_df = pd.DataFrame({
        'Month': forecast_index.strftime('%B %Y'),
        'Predicted Price (Rs./Quintal)': forecast_values.values
    })

    # Filter based on requested range
    forecast_df['MonthDate'] = pd.to_datetime(forecast_index)  # for filtering
    forecast_df = forecast_df[(forecast_df['MonthDate'] >= start_date) & 
                              (forecast_df['MonthDate'] <= end_date)]
    forecast_df.drop(columns='MonthDate', inplace=True)

    return forecast_df

@app.route('/')
def start():
    """
    Default route to render the start.html page.
    """
    return render_template('start.html')

@app.route('/predict', methods=['GET'])
def predict():
    """Prediction route."""
    crop = request.args.get('crop')
    center = request.args.get('center')
    start_date = request.args.get('start_date')  # Optional
    end_date = request.args.get('end_date')      # Optional

    if not crop or not center:
        return jsonify({"error": "Both crop and center must be selected."}), 400

    # Construct the dataset file name
    file_name = f"{crop}_{center}.csv".replace(" ", "_").lower()
    file_path = os.path.join(DATASET_DIR, file_name)

    if not os.path.exists(file_path):
        return jsonify({"error": f"Dataset for {crop} in {center} not found."}), 404

    try:
        # Preprocess the data
        preprocessor = TimeSeriesPreprocessor(file_path)
        preprocessor.load_data()
        processed_data = preprocessor.preprocess_data()

        # Train SARIMA model
        model = SARIMAModel(processed_data)
        model.fit_model()

        if start_date and end_date:
            # Custom forecast range (from July 2025 to December 2025)
            forecast_df = forecast_range(model, start_date, end_date)
            predictions = {
                "dates": forecast_df['Month'].tolist(),
                "prices": [round(p, 2) for p in forecast_df['Predicted Price (Rs./Quintal)']]
            }
        else:
            # Default: next 6 months (July 2025 to December 2025)
            forecast_dates, forecast_values = model.forecast(steps=6)
            predictions = {
                "dates": [date.strftime("%B %Y") for date in forecast_dates],
                "prices": [round(price, 2) for price in forecast_values]
            }

        return jsonify(predictions)

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        session['email'] = email  # Store email in session
        return redirect('/home')
    return render_template('login.html')


@app.route('/home')
def home():
    """
    Route to render the main index.html page.
    """
    return render_template('index.html')

@app.route('/send_report', methods=['POST'])
def send_report():
    """Handles report sending by generating predictions and sending an email."""

    # Retrieve user email from session
    user_email = session.get('email')
    if not user_email:
        return jsonify({"message": "User email not found. Please log in again."}), 401

    # Get the JSON data from the request
    data = request.get_json()
    crop = data.get('crop')
    center = data.get('center')
    graph_base64 = data.get('graphImage')

    if not crop or not center:
        return jsonify({"message": "Missing crop or center"}), 400

    # Construct dataset file path
    file_name = f"{crop}_{center}.csv".replace(" ", "_").lower()
    file_path = os.path.join(DATASET_DIR, file_name)

    # Check if the dataset exists
    if not os.path.exists(file_path):
        return jsonify({"message": "Dataset not found."}), 404

    try:
        # Initialize preprocessor and load data
        preprocessor = TimeSeriesPreprocessor(file_path)
        preprocessor.load_data()
        processed_data = preprocessor.preprocess_data()

        # Train SARIMA model
        model = SARIMAModel(processed_data)
        model.fit_model()

        # Use forecast_range to get predictions from July to December 2025
        forecast_df = forecast_range(model, '2025-07-01', '2025-12-31')

        # Prepare prediction response
        predictions = {
            "dates": forecast_df['Month'].tolist(),
            "prices": [round(p, 2) for p in forecast_df['Predicted Price (Rs./Quintal)'].tolist()]
        }

        # PDF Generation
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Border
        p.setLineWidth(2)
        p.rect(30, 30, width - 60, height - 60)

        # Title
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width / 2, height - 60, "CropFusion Report")

        # Subtitle
        p.setFont("Helvetica", 14)
        p.drawCentredString(width / 2, height - 80, "Forecasted Market Prices for Agricultural Crops")

        # Crop Details
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 120, f"Crop: {crop.capitalize()}")
        p.drawString(50, height - 140, f"Center: {center.capitalize()}")

        # Crop Image
        image_path = os.path.join("static", f"images/{crop.lower()}.jpg")
        if os.path.exists(image_path):
            try:
                p.drawImage(image_path, width - 190, height - 215, width=150, height=150, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print("Failed to load image:", e)

        # Table
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors

        # Table Data
        table_data = [["Month", "Predicted Price (Rs./Quintal)"]]
        for _, row in forecast_df.iterrows():
            table_data.append([row['Month'], f"Rs. {round(row['Predicted Price (Rs./Quintal)'], 2)}"])

        table = Table(table_data, colWidths=[200, 250])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        table_width, table_height = table.wrap(0, 0)
        table_x = (width - table_width) / 2
        table_y = height - 200
        table.wrapOn(p, width, height)
        table.drawOn(p, table_x, table_y - table_height)

        # Graph from base64
        if graph_base64 and graph_base64.startswith("data:image/png;base64,"):
            try:
                p.setFont("Helvetica-Bold", 12)
                p.drawCentredString(width / 2, 365, "Predicted Price Trend Graph")

                graph_data = base64.b64decode(graph_base64.split(",")[1])
                graph_img = Image.open(BytesIO(graph_data)).convert("RGB")
                graph_buffer = BytesIO()
                graph_img.save(graph_buffer, format='PNG')
                graph_buffer.seek(0)

                graph_width = 500
                graph_height = 270
                graph_x = (width - graph_width) / 2
                p.drawImage(ImageReader(graph_buffer), graph_x, 60, width=graph_width, height=graph_height)
            except Exception as e:
                print("Failed to render graph from base64:", e)
                
            print("Graph inserted at x:", graph_x, "width:", graph_width)


        p.showPage()
        p.save()
        buffer.seek(0)


        # Email setup
        msg = EmailMessage()
        msg['Subject'] = f"CropFusion Report - {crop} ({center})"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = user_email
        msg.set_content(f"Attached is the forecast report for {crop} in {center}.\nThank you for using CropFusion!")

        # Attach PDF
        msg.add_attachment(buffer.read(), maintype='application', subtype='pdf',
                           filename=f"{crop}_{center}_report.pdf")

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        return jsonify({"message": "Report sent to your email successfully!"})

    except Exception as e:
        print("Error sending report:", e)
        traceback.print_exc()
        return jsonify({"message": "Failed to generate or send report."}), 500

@app.route('/save_email', methods=['POST'])
def save_email():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"message": "Email is required"}), 400
    
     
    session['email'] = email  # ✅ Store it in Flask session
    return jsonify({"message": "Email saved to session"})

@app.route('/download_report', methods=['POST'])
def download_report():
    """Handles report download by generating predictions and returning a downloadable file."""

    # Get the JSON data from the request
    data = request.get_json()
    crop = data.get('crop')
    center = data.get('center')
    graph_base64 = data.get('graphImage')

    if not crop or not center:
        return jsonify({"message": "Missing crop or center"}), 400

    # Construct dataset file path
    file_name = f"{crop}_{center}.csv".replace(" ", "_").lower()
    file_path = os.path.join(DATASET_DIR, file_name)

    # Check if the dataset exists
    if not os.path.exists(file_path):
        return jsonify({"message": "Dataset not found."}), 404

    try:
        # Initialize preprocessor and load data
        preprocessor = TimeSeriesPreprocessor(file_path)
        preprocessor.load_data()  # Load the data
        processed_data = preprocessor.preprocess_data()  # Preprocess data

        # Train SARIMA model
        model = SARIMAModel(processed_data)
        model.fit_model()  # Fit the model

         # Use forecast_range to get predictions from July to December 2025
        forecast_df = forecast_range(model, '2025-07-01', '2025-12-31')

        # Prepare prediction response
        predictions = {
            "dates": forecast_df['Month'].tolist(),
            "prices": [round(p, 2) for p in forecast_df['Predicted Price (Rs./Quintal)'].tolist()]
        }

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Border
        p.setLineWidth(2)
        p.rect(30, 30, width - 60, height - 60)

        # Title
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width / 2, height - 60, "CropFusion Report")

        # Subtitle
        p.setFont("Helvetica", 14)
        p.drawCentredString(width / 2, height - 80, "Forecasted Market Prices for Agricultural Crops")

        # Crop Details
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 120, f"Crop: {crop.capitalize()}")
        p.drawString(50, height - 140, f"Center: {center.capitalize()}")

        # Crop Image
        image_path = os.path.join("static", f"images/{crop.lower()}.jpg")
        if os.path.exists(image_path):
            try:
               p.drawImage(image_path, width - 190, height - 215, width=150, height=150, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print("Failed to load image:", e)

        # Table Data
        table_data = [["Month", "Predicted Price (Rs./Quintal)"]]
        for _, row in forecast_df.iterrows():
            table_data.append([row['Month'], f"Rs. {round(row['Predicted Price (Rs./Quintal)'], 2)}"])


        # Table Creation & Styling
        table = Table(table_data, colWidths=[200, 250])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        table_width, table_height = table.wrap(0, 0)
        table_x = (width - table_width) / 2
        table_y = height - 200
        table.wrapOn(p, width, height)
        table.drawOn(p, table_x, table_y - table_height)

        # Graph Image (if provided)
        if graph_base64 and graph_base64.startswith("data:image/png;base64,"):
            try:
                p.setFont("Helvetica-Bold", 12)
                p.drawCentredString(width / 2, 365, "Predicted Price Trend Graph")

                graph_data = base64.b64decode(graph_base64.split(",")[1])
                graph_img = Image.open(BytesIO(graph_data)).convert("RGB")
                graph_buffer = BytesIO()
                graph_img.save(graph_buffer, format='PNG')
                graph_buffer.seek(0)

                graph_width = 500
                graph_height = 270
                graph_x = (width - graph_width) / 2
                p.drawImage(ImageReader(graph_buffer), graph_x, 60, width=graph_width, height=graph_height)
            except Exception as e:
                print("Failed to render graph from base64:", e)

        p.showPage()
        p.save()
        buffer.seek(0)

        return send_file(buffer, as_attachment=True,
                         download_name=f"{crop}_{center}_report.pdf",
                         mimetype='application/pdf')

    except Exception as e:
        print("Error generating report:", e)
        traceback.print_exc()
        return jsonify({"message": "Failed to generate report."}), 500

@app.route('/crop_conditions', methods=['GET'])
def crop_conditions():
    crop = request.args.get('crop')
    zone = request.args.get('zone')

    # Check if both crop and zone are provided
    if not crop or not zone:
        return jsonify({"error": "Both crop and zone must be selected."}), 400

    json_path = os.path.join(DATASET_DIR, "crop_conditions.json")

    try:
        with open(json_path, "r") as file:
            conditions_data = json.load(file)

        crop_lower = crop.lower()
        zone_lower = zone.capitalize()  # Ensure first letter is uppercase

        if crop_lower in conditions_data and zone_lower in conditions_data[crop_lower]:
            return jsonify(conditions_data[crop_lower][zone_lower])
        else:
            return jsonify({"error": "No data found for selected crop and zone."}), 404
    except Exception as e:
        print(f"Error loading crop conditions: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

  # Endpoint to get crop suggestions
@app.route('/get_crop_suggestions', methods=['GET'])
def get_crop_suggestions():
    crop = request.args.get('crop', '').strip().lower()
    selected_region = request.args.get('region', '').strip().lower()
    selected_zone = request.args.get('zone', '').strip().lower()

    # Clean crop name for matching
    crop = crop.replace('(', '').replace(')', '').replace('&', 'and')

    print("Crop:", crop)
    print("Region:", selected_region)   
    print("Zone:", selected_zone)

    try:
        with open(os.path.join(DATASET_DIR, 'crop_suggestions.json')) as f:
            raw_data = json.load(f)

        # Normalize crop keys for case-insensitive match
        normalized_data = {k.strip().lower(): v for k, v in raw_data.items()}
        print("Available crops:", list(normalized_data.keys()))

        if crop not in normalized_data:
            print("Crop not found in data")
            return jsonify([])

        # Fetch all regions for the selected crop
        all_regions = normalized_data[crop]

        # Prepare predictions for regions excluding selected_region
        profitable_regions = []

        for region_info in all_regions:
            region_name = region_info['region'].strip().lower()
            # Skip the chosen region
            if region_name == selected_region.strip().lower():
                continue

            # Fetch price data for this region
            file_path = os.path.join(DATASET_DIR, f"{crop}_{region_name}.csv".replace(" ", "_").lower())
            if not os.path.exists(file_path):
                continue  # Skip if no data file for this region

            preprocessor = TimeSeriesPreprocessor(file_path)
            preprocessor.load_data()
            processed_data = preprocessor.preprocess_data()

            model = SARIMAModel(processed_data)
            model.fit_model()
            forecast_dates, forecast_values = model.forecast(steps=12)

            # Calculate average predicted price for the top 10 filter later
            avg_predicted_price = np.mean(forecast_values)
            if np.isnan(avg_predicted_price):
                avg_predicted_price = None  # or use 0.0 as fallback if needed

            profitable_regions.append({
                "region": region_name,
                "reason": region_info["reason"],  # Existing reason from the JSON
                "soil": region_info["soil"],
                "rainfall": region_info["rainfall"],
                "temperature": region_info["temperature"],
                "avg_predicted_price": avg_predicted_price
                })

        # Sort regions by avg predicted price and get top 10
        # Filter out regions with None prices before sorting
        profitable_regions = [r for r in profitable_regions if r['avg_predicted_price'] is not None]

        # Now sort safely
        profitable_regions = sorted(profitable_regions, key=lambda x: x['avg_predicted_price'], reverse=True)[:10]

        return jsonify(profitable_regions)

    except Exception as e:
        print(f"Error loading crop suggestions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']  # user's email
        phone = request.form['phone']
        message = request.form['message']

        try:
            # Establish connection to SMTP server
            with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                connection.starttls()  # Secure the connection
                connection.login(user=EMAIL_ADDRESS, password=EMAIL_PASSWORD)  # Use App Password
                connection.sendmail(
                    from_addr=email,
                    to_addrs=EMAIL_ADDRESS,
                    msg=f"Subject: New Message from {name}\n\n"
                        f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
                )

            return "Email sent successfully!"

        except Exception as e:
            return f"Error: {e}"


if __name__ == "__main__":
    app.run(debug=True)