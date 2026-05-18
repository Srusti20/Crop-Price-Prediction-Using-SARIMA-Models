# Crop Price Prediction Using SARIMA Models

A comprehensive web application for predicting agricultural crop prices using SARIMA (Seasonal AutoRegressive Integrated Moving Average) time series forecasting models. The application provides farmers and agricultural professionals with data-driven insights to optimize their crop selection and pricing strategies.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Key Components](#key-components)
- [Contributing](#contributing)
- [License](#license)

---

## ✨ Features

### Core Functionality
- **Price Forecasting**: Predict crop prices for up to 12 months in advance using SARIMA models
- **Custom Date Range**: Generate predictions for user-specified time periods
- **Multi-Crop Support**: Support for multiple agricultural crops across different regions
- **Regional Analysis**: Compare profitability across different growing regions

### User Features
- **User Authentication**: Secure login system to manage user sessions
- **Interactive Dashboard**: Intuitive interface for crop selection and price visualization
- **Real-time Predictions**: Instant price forecasts based on historical data
- **Report Generation**: Download and email comprehensive PDF reports with predictions and graphs
- **Crop Recommendations**: Get suggestions for profitable alternative regions to grow selected crops
- **Growing Conditions**: View optimal soil, rainfall, and temperature conditions for crops

### Output Formats
- **Interactive Charts**: Visualize price trends with dynamic graphs
- **PDF Reports**: Professional reports with predictions, graphs, and crop images
- **Email Delivery**: Automated report delivery to user email addresses

---

## 🛠 Tech Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Time Series Model**: SARIMA from statsmodels
- **Data Processing**: Pandas, NumPy
- **PDF Generation**: ReportLab
- **Email Service**: Gmail SMTP

### Frontend
- **CSS Framework**: Materialize CSS v1.0.0-rc.2
- **Data Visualization**: Chart libraries (embedded in frontend)
- **Templating**: Jinja2

### Data Storage
- **Datasets**: CSV format (stored in `templates/` directory)
- **Configuration**: JSON files for crop conditions and suggestions

---

## 📦 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Node.js and npm (for Materialize CSS)
- Gmail account with App Password (for email functionality)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Srusti20/Crop-Price-Prediction-Using-SARIMA-Models.git
cd Crop-Price-Prediction-Using-SARIMA-Models
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies
```bash
npm install
```

### 5. Project Structure Setup
Ensure the following directories exist:
```
project-root/
├── templates/           # CSV datasets and JSON config files
├── static/
│   └── images/          # Crop images for reports
├── venv/               # Virtual environment
├── app.py              # Main Flask application
└── package.json        # Node.js dependencies
```

---

## ⚙️ Configuration

### Email Setup (Gmail SMTP)

Update credentials in `app.py`:
```python
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_gmail_app_password"  # Not your regular password
```

**Steps to Generate Gmail App Password:**
1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings → Security
3. Generate an App Password (select Mail and Windows Computer)
4. Use the generated password above

### Dataset Files
Place your CSV files in the `templates/` directory with the naming convention:
```
{crop_name}_{region_name}.csv
```

**Required CSV columns:**
- `Price Date` - Date of the price record
- `Modal Price (Rs./Quintal)` - Price value in Rs. per Quintal

### Configuration Files
Create in `templates/` directory:

**crop_conditions.json** - Growing conditions for crops
```json
{
  "wheat": {
    "North": {
      "soil": "Well-drained loamy soil",
      "rainfall": "400-600 mm",
      "temperature": "15-25°C"
    }
  }
}
```

**crop_suggestions.json** - Alternative regions and reasons
```json
{
  "wheat": [
    {
      "region": "North",
      "reason": "Optimal climate and soil conditions",
      "soil": "Well-drained loamy soil",
      "rainfall": "400-600 mm",
      "temperature": "15-25°C"
    }
  ]
}
```

---

## 📁 Project Structure

```
Crop-Price-Prediction-Using-SARIMA-Models/
│
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js dependencies
├── package-lock.json               # Dependency lock file
├── README.md                       # This file
│
├── templates/                      # Flask templates & datasets
│   ├── start.html                  # Landing page
│   ├── login.html                  # Login page
│   ├── index.html                  # Main dashboard
│   ├── *.csv                       # Price datasets
│   ├── crop_conditions.json        # Growing conditions data
│   └── crop_suggestions.json       # Region suggestions data
│
├── static/
│   └── images/                     # Crop images for reports
│       ├── wheat.jpg
│       ├── rice.jpg
│       └── ...
│
└── venv/                           # Python virtual environment
```

---

## 🎯 Usage

### Starting the Application
```bash
python app.py
```

The application will run on `http://localhost:5000`

### Workflow

1. **Landing Page** (`/`)
   - Welcome page with navigation to login

2. **Login** (`/login`)
   - Enter email address to access the dashboard
   - Email stored in session for report delivery

3. **Dashboard** (`/home`)
   - Select crop and growing region
   - View predicted prices for next 6 months
   - Visualize price trends on interactive graphs
   - Explore alternative profitable regions

4. **Generate Reports**
   - **Download**: Save PDF report locally
   - **Email**: Send report to registered email address

5. **View Conditions**
   - Check optimal growing conditions for selected crop
   - Get region-specific recommendations

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User login with email |
| POST | `/save_email` | Save email to session |

### Predictions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predict` | Get price predictions for crop & region |
| GET | `/crop_conditions` | Get growing conditions for crop & zone |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/download_report` | Download PDF report |
| POST | `/send_report` | Email PDF report to user |

### Recommendations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/get_crop_suggestions` | Get profitable alternative regions |

### Contact
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/send_message` | Send contact message via email |

### Example API Call
```bash
# Get price predictions
curl "http://localhost:5000/predict?crop=wheat&center=north"

# Get crop conditions
curl "http://localhost:5000/crop_conditions?crop=wheat&zone=North"

# Get region suggestions
curl "http://localhost:5000/get_crop_suggestions?crop=wheat&region=north&zone=north"
```

---

## 🧩 Key Components

### TimeSeriesPreprocessor
Handles data loading and preprocessing:
- Loads CSV datasets
- Validates required columns
- Converts data types
- Groups data by month
- Handles missing values (forward fill)

### SARIMAModel
Implements SARIMA forecasting:
- **Parameters**: ARIMA(2,1,2) × Seasonal(1,1,1,6)
- Trains on historical price data
- Generates future predictions
- Returns forecast with confidence intervals

### Report Generation
Creates professional PDF reports with:
- Crop name and region details
- Crop image
- Price prediction table
- Price trend visualization graph
- Professional formatting and styling

---

## 📊 Model Details

### SARIMA Configuration
```python
order=(2, 1, 2)              # ARIMA parameters
seasonal_order=(1, 1, 1, 6)  # Seasonal pattern (6-month cycle)
```

### Forecast Periods
- **Default**: Next 6 months (July - December 2025)
- **Custom**: User-specified date range
- **Maximum**: 12 months ahead

### Data Preprocessing
- **Frequency**: Monthly aggregation (average modal price)
- **Date Format**: ISO format (YYYY-MM-DD)
- **Missing Values**: Forward-fill method
- **Outliers**: Removed during validation

---

## ⚠️ Important Notes

### Email Security
- Never commit actual Gmail credentials to version control
- Use environment variables or `.env` file in production
- Store credentials securely using GitHub Secrets if deployed

### Dataset Requirements
- Ensure CSV files follow the naming convention: `{crop}_{region}.csv`
- All dates must be valid and in parseable format
- Price values must be numeric

### Session Management
- User email is stored in Flask session (non-persistent)
- Clear session data when logging out
- Sessions expire based on Flask configuration

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Dataset not found error
- **Solution**: Verify CSV file exists in `templates/` with correct naming convention

**Issue**: Email not sending
- **Solution**: Check Gmail credentials, enable 2FA, generate new App Password

**Issue**: SARIMA model fitting fails
- **Solution**: Ensure CSV has minimum historical data (recommended: 24+ months), check for data quality

**Issue**: Graphs not appearing in PDF
- **Solution**: Verify base64 image format, check PIL/Pillow installation

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📧 Contact & Support

For issues, questions, or suggestions:
- **GitHub Issues**: [Create an issue](https://github.com/Srusti20/Crop-Price-Prediction-Using-SARIMA-Models/issues)
- **Email**: Contact through the application's contact form

---

## 🙏 Acknowledgments

- SARIMA implementation via `statsmodels`
- UI design powered by Materialize CSS
- PDF generation using ReportLab
- Time series data analysis and visualization

---

**Last Updated**: 2026-05-18
