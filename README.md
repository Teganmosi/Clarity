# Clarity - Lead Scoring & Prioritization Engine

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A complete MVP for scoring and prioritizing leads for SMB sales teams using AI/ML. Built with Python + FastAPI (backend) and React + Tailwind CSS (frontend).

## 🚀 Features

### Backend (FastAPI + Python)

- **Lead Management**: Create, read, update, delete leads with full CRUD operations
- **Bulk Upload**: Import leads via CSV or JSON files
- **AI Lead Scoring**: Machine learning model (Logistic Regression) that predicts lead conversion probability
- **Analytics API**: Conversion rates, score distribution, trends, and performance metrics
- **Authentication**: API key and JWT token-based authentication
- **Notifications**: Email and Slack notifications for high-priority leads
- **CRM Integrations**: Mock endpoints for HubSpot and Pipedrive (easily extendable to real integrations)
- **Export**: Export leads to CSV or JSON format

### Frontend (React + Tailwind CSS)

- **Dashboard**: Overview of leads, conversions, and key metrics
- **Lead Management**: List, filter, sort, and manage leads
- **Upload Interface**: Drag-and-drop CSV/JSON file upload
- **Analytics Dashboard**: Interactive charts for conversion rates, score distribution, and trends
- **Integrations Panel**: Configure and sync with HubSpot/Pipedrive
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Mode**: Toggle between themes for better user experience

## 📁 Project Structure

```
lead-scoring-engine/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # SQLAlchemy database models
│   │   ├── schemas.py           # Pydantic validation schemas
│   │   ├── database.py          # Database connection and session
│   │   ├── auth.py              # Authentication logic
│   │   ├── scoring.py           # ML scoring engine
│   │   ├── notifications.py     # Email/Slack notifications
│   │   ├── integrations.py      # CRM integration handlers
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py          # Auth endpoints
│   │       ├── leads.py         # Lead CRUD endpoints
│   │       ├── analytics.py     # Analytics endpoints
│   │       └── integrations.py  # CRM sync endpoints
│   ├── requirements.txt
│   ├── .env.example
│   └── SETUP.md
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Analytics.jsx      # Analytics dashboard
│   │   │   ├── Dashboard.jsx     # Main dashboard
│   │   │   ├── Header.jsx        # Navigation header
│   │   │   ├── Integrations.jsx  # CRM integrations
│   │   │   ├── LeadsList.jsx     # Lead management
│   │   │   ├── Login.jsx        # Authentication
│   │   │   ├── LeadDetailModal.jsx # Lead details modal
│   │   │   └── ThemeToggle.jsx   # Dark/light mode toggle
│   │   ├── context/
│   │   │   └── ThemeContext.jsx  # Theme context provider
│   │   ├── services/
│   │   │   └── api.js          # API service layer
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── SETUP.md
├── sample-leads.csv
├── sample-leads.json
├── .gitignore
└── README.md
```

## 🎯 Quick Start

### Prerequisites

- **Backend**: Python 3.8+, pip
- **Frontend**: Node.js 16+, npm

### Backend Setup

1. Navigate to backend directory:

```bash
cd lead-scoring-engine/backend
```

2. Create virtual environment:

```bash
python -m venv venv
```

3. Activate virtual environment:

- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

6. Run the server:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:

```bash
cd lead-scoring-engine/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## 📖 Usage

### 1. Register/Login

- Visit `http://localhost:5173`
- Register a new account or login with existing credentials
- For MVP, password is optional - just use your username

### 2. Upload Leads

- Navigate to the Leads page
- Click "Upload" button
- Select CSV or JSON file
- Use provided sample files (`sample-leads.csv` or `sample-leads.json`) for testing
- Leads will be automatically scored on upload

### 3. View Ranked Leads

- Go to Leads page
- See leads sorted by score (highest first)
- Filter by source, campaign, status, score category, etc.
- Sort by score, date, name, or company
- Click on any lead to view detailed information

### 4. Analytics Dashboard

- Visit Analytics page
- View conversion rates and score distribution
- See performance by source and campaign
- Analyze lead trends over time

### 5. Configure Notifications

- High-priority leads (score >= 80) trigger automatic notifications
- Configure email settings in backend `.env`:
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
  - `NOTIFICATION_EMAIL`
- Configure Slack webhook in `.env`:
  - `SLACK_WEBHOOK_URL`

### 6. CRM Integrations

- Visit Integrations page
- Add API keys to backend `.env`:
  - `HUBSPOT_API_KEY` for HubSpot
  - `PIPEDRIVE_API_KEY` for Pipedrive
- Sync leads to CRM with one click

## 🔌 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Key Endpoints

#### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user
- `POST /auth/regenerate-api-key` - Regenerate API key

#### Leads

- `GET /leads/` - List leads with filters and pagination
- `POST /leads/` - Create new lead
- `GET /leads/{id}` - Get specific lead
- `PUT /leads/{id}` - Update lead
- `DELETE /leads/{id}` - Delete lead
- `POST /leads/bulk` - Bulk upload leads
- `POST /leads/upload/csv` - Upload CSV file
- `POST /leads/upload/json` - Upload JSON file
- `POST /leads/export` - Export leads
- `POST /leads/{id}/mark-converted` - Mark lead as converted
- `POST /leads/retrain-model` - Retrain ML model

#### Analytics

- `GET /analytics/conversion-rate` - Conversion rate metrics
- `GET /analytics/score-distribution` - Score distribution
- `GET /analytics/dashboard` - Full dashboard analytics
- `GET /analytics/source-performance` - Performance by source
- `GET /analytics/campaign-performance` - Performance by campaign
- `GET /analytics/trends` - Lead trends over time
- `GET /analytics/notifications-summary` - Notification summary

#### Integrations

- `GET /integrations/config` - Get integration config
- `POST /integrations/sync/hubspot` - Sync to HubSpot
- `POST /integrations/sync/pipedrive` - Sync to Pipedrive
- `GET /integrations/logs` - Get sync logs
- `GET /integrations/status` - Get integration status

## 🤖 Lead Scoring Model

The MVP uses a Logistic Regression model trained on:

- **Lead source**: website, referral, paid_ads, social_media, email, event, partner
- **Campaign type**: awareness, consideration, decision, retention
- **Marketing medium**: organic, cpc, cpm, email, referral, direct
- **Past interactions**: Number of previous engagements
- **Website engagement**: Pages visited, time on site
- **Company size**: startup, small, medium, large, enterprise
- **Budget level**: low, medium, high, enterprise
- **Email domain quality**: Corporate vs free email providers
- **Recency**: Time since last interaction

### Score Categories

- **🔥 Hot**: Score >= 80 - High priority, immediate follow-up
- **🌡️ Warm**: Score 50-79 - Medium priority, nurture
- **❄️ Cold**: Score < 50 - Low priority, monitor

### Model Retraining

The model can be retrained as more conversion data becomes available:

- Use the "Retrain Model" button in the frontend
- Or call `POST /leads/retrain-model` API endpoint
- Requires at least 10 leads with conversion status

## 🔧 Extending the System

### Adding New Scoring Features

Edit `backend/app/scoring.py` to add new features:

```python
# In _prepare_features method
df['new_feature'] = df['some_field'].map(mapping)

# In feature_columns list
self.feature_columns = [
    # ... existing columns
    'new_feature'
]
```

### Adding Real CRM Integrations

Edit `backend/app/integrations.py` and uncomment the actual API calls:

```python
# Uncomment for real HubSpot API
async with httpx.AsyncClient() as client:
    response = await client.post(
        self.base_url,
        json=contact_data,
        headers=headers,
        timeout=10.0
    )
    response.raise_for_status()
```

### Adding New Frontend Components

Add new components in `frontend/src/components/` and import them in `App.jsx`:

```jsx
// Add route in App.jsx
<Route path="/new-page" element={<NewComponent />} />
```

## ⚙️ Environment Variables

### Backend (.env)

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-secret-api-key-here

# Database
DATABASE_URL=sqlite:///./leads.db

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=alerts@yourcompany.com

# Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Lead Scoring
SCORE_THRESHOLD_HIGH=80
SCORE_THRESHOLD_MEDIUM=50

# CRM Integrations
HUBSPOT_API_KEY=your-hubspot-api-key
PIPEDRIVE_API_KEY=your-pipedrive-api-key
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## 📊 Sample Data

Sample lead files are provided for testing:

- `sample-leads.csv` - 15 sample leads in CSV format
- `sample-leads.json` - 10 sample leads in JSON format

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**

```bash
# Change port in .env or run with different port
python -m uvicorn app.main:app --port 8001
```

**Import errors:**

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**Database errors:**

```bash
# Delete database file and restart
rm leads.db  # Mac/Linux
del leads.db  # Windows
```

### Frontend Issues

**API connection errors:**

1. Ensure backend is running on `http://localhost:8000`
2. Check CORS settings in backend `.env`
3. Verify `VITE_API_URL` in frontend `.env`

**Build errors:**

```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```

## 🚀 Production Deployment

### Backend

1. Use production database (PostgreSQL, MySQL)
2. Set strong API keys and secrets
3. Use production WSGI server (Gunicorn, uWSGI)
4. Enable HTTPS
5. Set up proper logging and monitoring

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

Build and deploy to static hosting:

```bash
npm run build
# Deploy 'dist' directory to Vercel, Netlify, etc.
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with FastAPI for the backend API
- Frontend built with React and Vite
- Styled with Tailwind CSS
- Charts powered by Recharts
- Icons from Lucide React

## 📧 Support

For issues or questions, please refer to the setup guides:

- Backend: `backend/SETUP.md`
- Frontend: `frontend/SETUP.md`

Or open an issue in the GitHub repository.

---

**Built with ❤️ for sales teams who want to prioritize their leads effectively**
