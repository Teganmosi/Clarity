# Lead Scoring Engine - Comprehensive Codebase Analysis

## Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Data Flow & Component Interactions](#data-flow--component-interactions)
6. [Function Reference](#function-reference)

---

## System Overview

The Lead Scoring Engine is a full-stack application that uses machine learning to score and prioritize leads for sales teams. It consists of:

- **Backend**: FastAPI (Python) with SQLite database, ML scoring engine, and CRM integrations
- **Frontend**: React (JavaScript) with Tailwind CSS for UI
- **Communication**: RESTful API with JWT and API key authentication

### Key Features

1. Lead CRUD operations with automatic scoring
2. Bulk lead upload (CSV/JSON)
3. ML-based lead scoring (Logistic Regression)
4. Analytics dashboard with charts
5. Email/Slack notifications for high-priority leads
6. CRM integrations (HubSpot, Pipedrive)
7. Export functionality

---

## Backend Architecture

### Project Structure

```
backend/app/
├── main.py              # FastAPI application entry point
├── database.py          # Database connection and session management
├── models.py             # SQLAlchemy ORM models
├── schemas.py            # Pydantic validation schemas
├── auth.py               # Authentication logic
├── scoring.py            # ML scoring engine
├── notifications.py      # Email/Slack notifications
├── integrations.py       # CRM integration handlers
└── routers/
    ├── auth.py           # Authentication endpoints
    ├── leads.py          # Lead CRUD endpoints
    ├── analytics.py      # Analytics endpoints
    └── integrations.py   # CRM sync endpoints
```

### Core Components

#### 1. main.py - Application Entry Point

**Purpose**: Initializes the FastAPI application, configures middleware, and includes routers.

**Key Functions**:

- `lifespan()`: Manages startup (database initialization) and shutdown events
- `root()`: Returns API information
- `health_check()`: Health check endpoint

**How it works**:

1. Loads environment variables
2. Sets up logging
3. Creates FastAPI app with CORS middleware
4. Includes routers for different features
5. Runs on configurable host/port

**Connections**:

- Calls `init_db()` from database.py on startup
- Includes routers from routers/ directory
- Handles global exceptions

---

#### 2. database.py - Database Management

**Purpose**: Manages SQLite database connection and sessions.

**Key Functions**:

- `get_db()`: Dependency that provides database sessions
- `init_db()`: Creates database tables on startup

**How it works**:

1. Creates SQLAlchemy engine using DATABASE_URL
2. Defines SessionLocal class for database sessions
3. Creates all tables from Base metadata on init
4. Provides get_db() generator for FastAPI dependency injection

**Connections**:

- Used by all routers to get database sessions
- Called by main.py lifespan manager

---

#### 3. models.py - Database Models

**Purpose**: Defines database tables using SQLAlchemy ORM.

**Models**:

##### User Model

```python
- id: Primary key
- username: Unique identifier
- email: Unique email
- hashed_password: Bcrypt hash (optional)
- api_key: Unique API key for authentication
- is_active: Boolean status
- created_at, updated_at: Timestamps
- leads: Relationship to Lead model
```

**Purpose**: Stores user authentication information and API keys.

##### Lead Model

```python
- id: Primary key
- user_id: Foreign key to User
- name, email: Required fields
- company, phone, title: Optional contact info
- source, campaign, medium: Lead origin tracking
- past_interactions: Number of previous engagements
- pages_visited, time_on_site: Engagement metrics
- company_size, industry, budget: Qualification data
- score: 0-100 conversion probability
- score_category: hot/warm/cold
- conversion_probability: Decimal probability
- status: new/contacted/qualified/converted/lost
- converted, conversion_date: Conversion tracking
- hubspot_id, pipedrive_id: External CRM IDs
- notes, tags: Additional metadata
- created_at, updated_at: Timestamps
```

**Purpose**: Stores lead information and scores.

##### NotificationLog Model

```python
- id: Primary key
- lead_id: Foreign key to Lead
- notification_type: email/slack
- recipient, subject, message: Notification details
- status: sent/failed
- error_message: Failure details
- sent_at: Timestamp
```

**Purpose**: Logs all notifications sent for audit trail.

##### IntegrationLog Model

```python
- id: Primary key
- lead_id: Foreign key to Lead
- integration_type: hubspot/pipedrive
- action: create/update/sync
- external_id: CRM record ID
- request_data, response_data: HTTP payload details
- status: success/failed
- error_message: Failure details
- created_at: Timestamp
```

**Purpose**: Logs all CRM integration activities.

**Connections**:

- User has one-to-many relationship with Lead
- Lead belongs to User
- All models use Base from database.py

---

#### 4. auth.py - Authentication System

**Purpose**: Handles user authentication using JWT tokens and API keys.

**Key Functions**:

##### `verify_password(plain_password, hashed_password)`

- **Purpose**: Verifies password against bcrypt hash
- **Returns**: Boolean
- **Uses**: pwd_context from passlib

##### `get_password_hash(password)`

- **Purpose**: Hashes password using bcrypt
- **Returns**: Hashed password string

##### `generate_api_key()`

- **Purpose**: Generates secure random API key
- **Returns**: String like "lsk\_..." (32 random characters)
- **Uses**: secrets.token_urlsafe()

##### `create_access_token(data, expires_delta)`

- **Purpose**: Creates JWT access token
- **Parameters**:
  - data: Dictionary to encode (typically {"sub": username})
  - expires_delta: Optional timedelta (default 24 hours)
- **Returns**: JWT token string
- **Uses**: jose library with HS256 algorithm

##### `verify_token(token)`

- **Purpose**: Verifies and decodes JWT token
- **Returns**: Decoded payload dict or None if invalid
- **Catches**: JWTError exceptions

##### `get_current_user_by_api_key(api_key, db)`

- **Purpose**: Authenticates user via API key
- **Depends**: api_key_header, get_db
- **Returns**: User object
- **Throws**: 401 if API key missing or invalid

##### `get_current_user_by_token(credentials, db)`

- **Purpose**: Authenticates user via JWT token
- **Depends**: bearer_scheme, get_db
- **Returns**: User object
- **Throws**: 401 if token missing or invalid

##### `get_current_user(api_key, credentials, db)`

- **Purpose**: Authenticates using either API key or JWT token
- **Logic**:
  1. Tries API key first
  2. Falls back to JWT token
  3. Throws 401 if both fail
- **Returns**: User object

##### `create_user(db, username, email, password)`

- **Purpose**: Creates new user in database
- **Process**:
  1. Generates API key
  2. Hashes password if provided
  3. Creates User record
  4. Commits to database
- **Returns**: Created User object

##### `authenticate_user(db, username, password)`

- **Purpose**: Validates user credentials
- **Process**:
  1. Queries user by username
  2. Verifies password if hashed_password exists
  3. For backward compatibility, allows auth without password
- **Returns**: User object or None

##### `verify_admin_key(api_key)`

- **Purpose**: Checks if API key is admin key
- **Returns**: Boolean
- **Uses**: ADMIN_API_KEY environment variable

**Connections**:

- Used by auth router for registration/login
- Used by all routers for authentication via get_current_user
- Depends on database.py for User model

---

#### 5. scoring.py - ML Scoring Engine

**Purpose**: Machine learning-based lead scoring using Logistic Regression.

**Class: LeadScoringEngine**

##### `__init__(model_path)`

- **Purpose**: Initialize scoring engine
- **Process**:
  1. Sets up model, scaler, feature_columns
  2. Creates models directory if needed
  3. Loads existing model from disk or initializes default
- **Parameters**: model_path (default: "models/lead_scoring_model.pkl")

##### `_prepare_features(leads)`

- **Purpose**: Convert lead data to ML features
- **Process**:
  1. Converts to pandas DataFrame
  2. Converts numeric columns (past_interactions, pages_visited, time_on_site)
  3. Applies feature weights/mappings:
     - source_weights: website(0.5), referral(0.7), paid_ads(0.4), etc.
     - campaign_weights: awareness(0.3), consideration(0.5), decision(0.7), etc.
     - medium_weights: organic(0.6), cpc(0.4), email(0.5), etc.
     - company_size_weights: startup(0.4), small(0.5), enterprise(0.8), etc.
     - budget_weights: low(0.2), medium(0.5), high(0.7), enterprise(0.9)
  4. Calculates engineered features:
     - source_score, campaign_score, medium_score
     - company_size_score, budget_score
     - email_domain_quality: 0.8 for corporate, 0.5 for free email providers
     - interaction_score: past_interactions \* 0.06
     - engagement_score: (pages_visited _ 0.03) + (time_on_site _ 0.015)
     - recency_score: Based on last_interaction_date
       - ≤1 day: 1.0, ≤7 days: 0.8, ≤30 days: 0.6, ≤90 days: 0.4, >90: 0.2
  5. Returns DataFrame with feature columns
- **Returns**: DataFrame with prepared features

##### `_get_email_domain_quality(email)`

- **Purpose**: Score email domain quality
- **Returns**: 0.8 for corporate domains, 0.5 for free email providers (gmail, outlook, hotmail, yahoo)

##### `_calculate_recency_score(date)`

- **Purpose**: Calculate recency score based on last interaction
- **Returns**: 1.0 (≤1 day), 0.8 (≤7 days), 0.6 (≤30 days), 0.4 (≤90 days), 0.2 (>90 days)

##### `train(leads, labels)`

- **Purpose**: Train ML model on lead data
- **Process**:
  1. Prepares features from leads
  2. Splits data (80/20) using train_test_split
  3. Scales features using StandardScaler
  4. Trains LogisticRegression with balanced class weights
  5. Evaluates accuracy
  6. Saves model to disk
- **Returns**: Dictionary with accuracy and feature_importance
- **Requirements**: At least 10 leads with 2+ in each class

##### `predict(leads)`

- **Purpose**: Predict conversion probability for leads
- **Process**:
  1. If model not trained, uses heuristic scoring
  2. Prepares features
  3. Scales features using trained scaler
  4. Predicts probabilities using model.predict_proba()
  5. Adds score, conversion_probability, score_category to each lead
- **Returns**: List of leads with scores

##### `_heuristic_score(leads)`

- **Purpose**: Fallback scoring when model not trained
- **Algorithm**:
  1. Base score: 30.0
  2. Add source bonus: referral(+15), website(+8), email(+10), paid_ads(+3), etc.
  3. Add engagement bonus:
     - past_interactions \* 3 (max 15)
     - pages_visited \* 1.5 (max 8)
     - time_on_site \* 0.3 (max 4)
  4. Add company size bonus: enterprise(+12), large(+8), medium(+4), small(0), startup(-3)
  5. Add budget bonus: enterprise(+12), high(+8), medium(+4), low(-3)
  6. Add email domain bonus: +8 for corporate domains
  7. Add campaign bonus: decision(+10), consideration(+6), retention(+4), awareness(+2)
  8. Add medium bonus: referral(+8), organic(+5), direct(+4), email(+5), cpc(+3), cpm(+2)
  9. Clamp to 0-100
- **Returns**: List of leads with heuristic scores

##### `_get_score_category(score)`

- **Purpose**: Categorize lead by score
- **Returns**: "hot" (≥80), "warm" (50-79), "cold" (<50)

##### `retrain(db)`

- **Purpose**: Retrain model with all leads from database
- **Process**:
  1. Queries all leads with conversion status
  2. Validates minimum requirements (10 leads, 2+ in each class)
  3. Prepares lead dictionaries and labels
  4. Calls train() method
  5. Updates all lead scores in database
  6. Commits changes
- **Returns**: Training metrics

##### `_save_model()`

- **Purpose**: Save model, scaler, and configuration to disk
- **Format**: Pickle file with dictionary containing model, scaler, label_encoders, feature_columns, is_trained

##### `_load_model()`

- **Purpose**: Load model from disk
- **Process**: Opens pickle file and loads model data
- **Fallback**: Initializes default untrained model if load fails

##### `_initialize_default_model()`

- **Purpose**: Initialize untrained LogisticRegression model
- **Sets**: is_trained = False

**Global Functions**:

##### `score_leads(leads)`

- **Purpose**: Score a list of leads
- **Uses**: Global scoring_engine instance
- **Returns**: Scored leads

##### `retrain_model(db)`

- **Purpose**: Retrain the scoring model
- **Uses**: Global scoring_engine instance
- **Returns**: Training metrics

**Connections**:

- Called by leads router when creating/updating leads
- Used by integrations to score leads before CRM sync
- Model saved to disk for persistence

---

#### 6. routers/leads.py - Lead Management Endpoints

**Purpose**: Handles all lead CRUD operations, scoring, and bulk operations.

**Key Endpoints**:

##### POST /leads/ - Create Lead

- **Purpose**: Create new lead with automatic scoring
- **Process**:
  1. Scores lead using scoring_engine.predict()
  2. Creates Lead record with score
  3. Sends notification if score ≥ 80
- **Returns**: Created Lead object
- **Authentication**: Requires API key or JWT token

##### GET /leads/ - List Leads

- **Purpose**: List leads with filtering and pagination
- **Query Parameters**:
  - source, campaign, status, score_category, company_size, industry
  - score_min, score_max: Score range filters
  - converted: Boolean filter
  - page: Page number (default 1)
  - page_size: Items per page (default 20, max 100)
  - sort_by: score/created_at/name/company (default score)
  - sort_order: asc/desc (default desc)
- **Process**:
  1. Builds query with user filter
  2. Applies all filters
  3. Gets total count
  4. Applies sorting
  5. Applies pagination (offset/limit)
- **Returns**: {leads, total, page, page_size}

##### GET /leads/{lead_id} - Get Lead

- **Purpose**: Get specific lead by ID
- **Returns**: Lead object
- **Throws**: 404 if not found or not owned by user

##### PUT /leads/{lead_id} - Update Lead

- **Purpose**: Update lead with automatic re-scoring
- **Process**:
  1. Checks if scoring-relevant fields updated
  2. Updates lead fields
  3. Re-scores if needed
  4. Commits changes
- **Scoring-relevant fields**: source, campaign, medium, past_interactions, pages_visited, time_on_site, company_size, budget
- **Returns**: Updated Lead object

##### DELETE /leads/{lead_id} - Delete Lead

- **Purpose**: Delete lead
- **Returns**: 204 No Content
- **Throws**: 404 if not found

##### POST /leads/bulk - Bulk Upload

- **Purpose**: Upload multiple leads at once
- **Request Body**: {leads: [lead_objects]}
- **Process**:
  1. Scores all leads
  2. Creates Lead records in database
  3. Sends notifications for high-priority leads (score ≥ 80)
  4. Handles errors individually per lead
- **Returns**: {success_count, failed_count, leads, errors}

##### POST /leads/upload/csv - Upload CSV

- **Purpose**: Upload leads from CSV file
- **Required Columns**: name, email
- **Optional Columns**: company, phone, title, source, campaign, medium, past_interactions, pages_visited, time_on_site, company_size, industry, budget, notes, tags
- **Process**:
  1. Reads CSV file using pandas
  2. Validates required columns
  3. Converts to list of dictionaries
  4. Scores all leads
  5. Creates Lead records
  6. Sends notifications for high-priority leads
  7. Handles errors individually per row
- **Returns**: {success_count, failed_count, leads, errors}

##### POST /leads/upload/json - Upload JSON

- **Purpose**: Upload leads from JSON file
- **Format**: Array of lead objects
- **Required Fields**: name, email
- **Process**: Same as CSV upload but with JSON parsing
- **Returns**: {success_count, failed_count, leads, errors}

##### POST /leads/export - Export Leads

- **Purpose**: Export leads to CSV or JSON
- **Request Body**: {format: "csv"|"json", filters: {...}}
- **Process**:
  1. Builds query with user filter
  2. Applies optional filters
  3. Applies sorting
  4. Converts leads to dictionaries
  5. Generates CSV or JSON file
  6. Returns file as StreamingResponse
- **Returns**: File download

##### POST /leads/{lead_id}/mark-converted - Mark Converted

- **Purpose**: Mark lead as converted
- **Process**:
  1. Sets converted = True
  2. Sets conversion_date = now
  3. Sets status = "converted"
  4. Commits changes
- **Returns**: Updated Lead object

##### POST /leads/retrain-model - Retrain Model

- **Purpose**: Retrain ML scoring model
- **Process**: Calls scoring_engine.retrain(db)
- **Returns**: Training metrics

**Connections**:

- Uses models.py for Lead model
- Uses auth.py for authentication
- Uses scoring.py for lead scoring
- Uses notifications.py for high-priority alerts

---

#### 7. routers/analytics.py - Analytics Endpoints

**Purpose**: Provides analytics endpoints for conversion rates, score distribution, and insights.

**Key Endpoints**:

##### GET /analytics/conversion-rate - Conversion Rate

- **Purpose**: Get conversion rate analytics
- **Returns**: {
  total_leads: int,
  converted_leads: int,
  conversion_rate: float,
  by_source: {source: {total, converted, conversion_rate}},
  by_campaign: {campaign: {total, converted, conversion_rate}}
  }
- **Calculations**:
  - Total: Count of all leads for user
  - Converted: Count where converted=True
  - Rate: (converted/total \* 100)
  - By source/campaign: Grouped aggregation

##### GET /analytics/score-distribution - Score Distribution

- **Purpose**: Get score distribution analytics
- **Returns**: {
  hot: int (score ≥ 80),
  warm: int (50 ≤ score < 80),
  cold: int (score < 50),
  average_score: float,
  score_ranges: {'0-20', '21-40', '41-60', '61-80', '81-100'}
  }

##### GET /analytics/dashboard - Dashboard Analytics

- **Purpose**: Get complete dashboard analytics
- **Returns**: {
  conversion_rate: {...},
  score_distribution: {...},
  recent_activity: [{type, lead_id, lead_name, lead_email, score, score_category, timestamp}]
  }
- **Recent Activity**: Last 7 days of new leads and conversions (max 15 items)

##### GET /analytics/source-performance - Source Performance

- **Purpose**: Get performance metrics by lead source
- **Returns**: Array of {
  source: string,
  total_leads: int,
  average_score: float,
  converted_leads: int,
  conversion_rate: float
  }
- **Sorted**: By conversion_rate descending

##### GET /analytics/campaign-performance - Campaign Performance

- **Purpose**: Get performance metrics by campaign
- **Returns**: Array of {
  campaign: string,
  total_leads: int,
  average_score: float,
  converted_leads: int,
  conversion_rate: float
  }
- **Sorted**: By conversion_rate descending

##### GET /analytics/trends - Trends

- **Purpose**: Get lead trends over time
- **Query Parameters**: days (default 30)
- **Returns**: Array of {
  date: string,
  leads: int,
  conversions: int,
  average_score: float
  }
- **Includes**: All dates in range, even with zero values

##### GET /analytics/notifications-summary - Notifications Summary

- **Purpose**: Get summary of sent notifications
- **Returns**: {
  total_notifications: int,
  by_type: {email: int, slack: int},
  success_rate: float,
  recent_notifications: [{id, lead_id, notification_type, recipient, subject, status, sent_at}]
  }

**Connections**:

- Uses models.py for Lead and NotificationLog models
- Uses auth.py for authentication
- Uses SQLAlchemy aggregations (func.count, func.avg, func.sum)

---

#### 8. routers/integrations.py - CRM Integrations

**Purpose**: Handles CRM integrations (HubSpot, Pipedrive).

**Key Endpoints**:

##### GET /integrations/config - Get Config

- **Purpose**: Get current integration configuration
- **Returns**: {
  hubspot_api_key: string (masked),
  pipedrive_api_key: string (masked),
  hubspot_enabled: boolean,
  pipedrive_enabled: boolean
  }

##### POST /integrations/sync/hubspot - Sync to HubSpot

- **Purpose**: Sync leads to HubSpot CRM
- **Request Body**: {lead_ids: [int], sync_all: boolean}
- **Process**:
  1. Gets leads to sync (all or specific IDs)
  2. Calls bulk_sync_to_hubspot() from integrations.py
  3. Returns sync results
- **Returns**: {success, synced_count, failed_count, errors}

##### POST /integrations/sync/pipedrive - Sync to Pipedrive

- **Purpose**: Sync leads to Pipedrive CRM
- **Request Body**: {lead_ids: [int], sync_all: boolean}
- **Process**: Same as HubSpot sync
- **Returns**: {success, synced_count, failed_count, errors}

##### POST /integrations/sync/{lead_id}/hubspot - Sync Single Lead to HubSpot

- **Purpose**: Sync single lead to HubSpot
- **Process**:
  1. Gets lead by ID
  2. Calls sync_to_hubspot() from integrations.py
  3. Updates lead.hubspot_id if successful
- **Returns**: {success, message, hubspot_id}

##### POST /integrations/sync/{lead_id}/pipedrive - Sync Single Lead to Pipedrive

- **Purpose**: Sync single lead to Pipedrive
- **Process**: Same as HubSpot single sync
- **Returns**: {success, message, pipedrive_id}

##### GET /integrations/logs - Get Integration Logs

- **Purpose**: Get integration logs
- **Query Parameters**: integration_type (optional), limit (default 50)
- **Returns**: Array of {
  id, lead_id, integration_type, action, external_id, status, error_message, created_at
  }

##### GET /integrations/status - Get Integration Status

- **Purpose**: Get overall integration status
- **Returns**: {
  hubspot: {enabled, synced_leads, unsynced_leads},
  pipedrive: {enabled, synced_leads, unsynced_leads},
  total_leads: int,
  recent_syncs: [...]
  }

**Connections**:

- Uses models.py for Lead and IntegrationLog models
- Uses integrations.py for sync functions
- Uses auth.py for authentication

---

## Frontend Architecture

### Project Structure

```
frontend/src/
├── main.jsx              # React entry point
├── App.jsx               # Main app component with routing
├── components/
│   ├── Login.jsx         # Login/Register component
│   ├── Dashboard.jsx     # Main dashboard
│   ├── LeadsList.jsx     # Lead management
│   ├── Analytics.jsx     # Analytics dashboard
│   ├── Integrations.jsx  # CRM integrations
│   └── Header.jsx        # Navigation header
└── services/
    └── api.js            # API service layer
```

### Core Components

#### 1. api.js - API Service Layer

**Purpose**: Centralized API client for all backend communication.

**Key Functions**:

##### `apiRequest(endpoint, options)`

- **Purpose**: Generic API request handler
- **Process**:
  1. Constructs full URL from API_BASE_URL
  2. Adds authentication headers (API key or JWT token)
  3. Makes fetch request
  4. Handles errors
- **Authentication**: Tries API key first, then JWT token
- **Returns**: JSON response
- **Throws**: Error on failure

##### `authAPI.register(username, email)`

- **Purpose**: Register new user
- **Method**: POST /auth/register
- **Returns**: User object with API key

##### `authAPI.login(username, password)`

- **Purpose**: Login user
- **Method**: POST /auth/login (FormData)
- **Process**:
  1. Sends login request
  2. Stores API key in localStorage
  3. Stores auth token in localStorage
  4. Stores user object in localStorage
- **Returns**: User data and tokens

##### `authAPI.getCurrentUser()`

- **Purpose**: Get current user
- **Method**: GET /auth/me
- **Returns**: User object

##### `authAPI.regenerateApiKey()`

- **Purpose**: Regenerate API key
- **Method**: POST /auth/regenerate-api-key
- **Process**: Updates localStorage with new API key
- **Returns**: New API key

##### `authAPI.logout()`

- **Purpose**: Clear authentication data
- **Process**: Removes apiKey, authToken, user from localStorage

##### `leadsAPI.getLeads(params)`

- **Purpose**: Get all leads with filters and pagination
- **Method**: GET /leads/
- **Parameters**: source, campaign, status, score_min, score_max, score_category, company_size, industry, converted, page, page_size, sort_by, sort_order
- **Returns**: {leads, total, page, page_size}

##### `leadsAPI.getLead(leadId)`

- **Purpose**: Get single lead
- **Method**: GET /leads/{id}
- **Returns**: Lead object

##### `leadsAPI.createLead(leadData)`

- **Purpose**: Create new lead
- **Method**: POST /leads/
- **Returns**: Created Lead object

##### `leadsAPI.updateLead(leadId, leadData)`

- **Purpose**: Update lead
- **Method**: PUT /leads/{id}
- **Returns**: Updated Lead object

##### `leadsAPI.deleteLead(leadId)`

- **Purpose**: Delete lead
- **Method**: DELETE /leads/{id}
- **Returns**: Success response

##### `leadsAPI.bulkUpload(leads)`

- **Purpose**: Bulk upload leads
- **Method**: POST /leads/bulk
- **Returns**: {success_count, failed_count, leads, errors}

##### `leadsAPI.uploadCSV(file)`

- **Purpose**: Upload CSV file
- **Method**: POST /leads/upload/csv (FormData)
- **Returns**: {success_count, failed_count, leads, errors}

##### `leadsAPI.uploadJSON(file)`

- **Purpose**: Upload JSON file
- **Method**: POST /leads/upload/json (FormData)
- **Returns**: {success_count, failed_count, leads, errors}

##### `leadsAPI.exportLeads(exportRequest)`

- **Purpose**: Export leads
- **Method**: POST /leads/export
- **Parameters**: {format: "csv"|"json", filters: {...}}
- **Returns**: File blob for download

##### `leadsAPI.markConverted(leadId)`

- **Purpose**: Mark lead as converted
- **Method**: POST /leads/{id}/mark-converted
- **Returns**: Updated Lead object

##### `leadsAPI.retrainModel()`

- **Purpose**: Retrain ML model
- **Method**: POST /leads/retrain-model
- **Returns**: Training metrics

##### `analyticsAPI.getConversionRate()`

- **Purpose**: Get conversion rate analytics
- **Method**: GET /analytics/conversion-rate
- **Returns**: Conversion rate data

##### `analyticsAPI.getScoreDistribution()`

- **Purpose**: Get score distribution
- **Method**: GET /analytics/score-distribution
- **Returns**: Score distribution data

##### `analyticsAPI.getDashboard()`

- **Purpose**: Get dashboard analytics
- **Method**: GET /analytics/dashboard
- **Returns**: Complete dashboard data

##### `analyticsAPI.getSourcePerformance()`

- **Purpose**: Get source performance
- **Method**: GET /analytics/source-performance
- **Returns**: Array of source performance metrics

##### `analyticsAPI.getCampaignPerformance()`

- **Purpose**: Get campaign performance
- **Method**: GET /analytics/campaign-performance
- **Returns**: Array of campaign performance metrics

##### `analyticsAPI.getTrends(days)`

- **Purpose**: Get trends
- **Method**: GET /analytics/trends?days={days}
- **Returns**: Array of trend data points

##### `analyticsAPI.getNotificationsSummary()`

- **Purpose**: Get notifications summary
- **Method**: GET /analytics/notifications-summary
- **Returns**: Notifications summary data

##### `integrationsAPI.getConfig()`

- **Purpose**: Get integration config
- **Method**: GET /integrations/config
- **Returns**: Integration configuration

##### `integrationsAPI.syncToHubSpot(syncRequest)`

- **Purpose**: Sync to HubSpot
- **Method**: POST /integrations/sync/hubspot
- **Returns**: Sync results

##### `integrationsAPI.syncToPipedrive(syncRequest)`

- **Purpose**: Sync to Pipedrive
- **Method**: POST /integrations/sync/pipedrive
- **Returns**: Sync results

##### `integrationsAPI.syncLeadToHubSpot(leadId)`

- **Purpose**: Sync single lead to HubSpot
- **Method**: POST /integrations/sync/{id}/hubspot
- **Returns**: Sync result with HubSpot ID

##### `integrationsAPI.syncLeadToPipedrive(leadId)`

- **Purpose**: Sync single lead to Pipedrive
- **Method**: POST /integrations/sync/{id}/pipedrive
- **Returns**: Sync result with Pipedrive ID

##### `integrationsAPI.getLogs(params)`

- **Purpose**: Get integration logs
- **Method**: GET /integrations/logs
- **Parameters**: integration_type, limit
- **Returns**: Array of log entries

##### `integrationsAPI.getStatus()`

- **Purpose**: Get integration status
- **Method**: GET /integrations/status
- **Returns**: Integration status data

**Connections**:

- Used by all React components
- Centralizes authentication handling
- Provides consistent error handling

---

#### 2. App.jsx - Main Application Component

**Purpose**: Handles routing and authentication state.

**State**:

- `user`: Current user object (from localStorage)
- `loading`: Boolean for loading state

**Key Functions**:

##### `useEffect` (on mount)

- **Purpose**: Check if user is logged in
- **Process**: Loads user from localStorage
- **Effect**: Runs once on component mount

##### `handleLogin(userData)`

- **Purpose**: Handle successful login
- **Process**: Sets user state from userData.user
- **Called by**: Login component

##### `handleLogout()`

- **Purpose**: Handle logout
- **Process**:
  1. Calls api.auth.logout()
  2. Sets user state to null
- **Called by**: Header component

**Routing**:

- `/` → Redirects to `/dashboard`
- `/dashboard` → Dashboard component
- `/leads` → LeadsList component
- `/analytics` → Analytics component
- `/integrations` → Integrations component
- Not logged in → Login component

**Conditional Rendering**:

- Loading: Shows "Loading..." spinner
- Not logged in: Shows Login component
- Logged in: Shows Router with Header and main content

**Connections**:

- Uses api.js for authentication
- Wraps all route components
- Provides user context to children

---

#### 3. Login.jsx - Login/Register Component

**Purpose**: User authentication (login and registration).

**State**:

- `isLogin`: Boolean (true for login, false for register)
- `username`: String
- `password`: String (optional)
- `email`: String (for registration)
- `loading`: Boolean
- `error`: String

**Key Functions**:

##### `handleSubmit(e)`

- **Purpose**: Handle form submission
- **Process**:
  1. If login: Calls api.auth.login(username, password)
  2. If register: Calls api.auth.register(username, email)
  3. On success: Calls onLogin(userData)
  4. On error: Sets error message
- **Called by**: Form submit button

##### `toggleMode()`

- **Purpose**: Toggle between login and register
- **Process**: Flips isLogin state, clears form

**UI Components**:

- Login form: Username + password (password optional for MVP)
- Register form: Username + email
- Error display: Shows error message if present
- Toggle link: Switch between login/register

**Connections**:

- Uses api.js for authentication
- Calls onLogin callback on successful auth
- Controlled by App.jsx routing

---

#### 4. Dashboard.jsx - Main Dashboard

**Purpose**: Shows overview of leads, analytics, and quick actions.

**State**:

- `analytics`: Dashboard analytics data
- `loading`: Boolean
- `error`: String

**Key Functions**:

##### `loadDashboard()`

- **Purpose**: Load dashboard data
- **Process**: Calls api.analytics.getDashboard()
- **Called by**: useEffect on mount

##### `useEffect` (analytics dependency)

- **Purpose**: Reload analytics when data changes
- **Effect**: Runs on component mount

**Sub-components**:

##### StatCard

- **Purpose**: Display single metric
- **Props**: title, value, icon, color
- **Renders**: Icon + title + value with color coding

##### ScoreCategoryCard

- **Purpose**: Display score category (hot/warm/cold)
- **Props**: title, count, icon, color, description
- **Renders**: Icon + count + title + description

##### ActivityItem

- **Purpose**: Display recent activity item
- **Props**: activity object
- **Renders**: Icon + activity text + timestamp + score badge

##### QuickAction

- **Purpose**: Quick action link card
- **Props**: title, description, icon, link
- **Renders**: Icon + title + description as Link

**Data Displayed**:

- Total leads
- Converted leads
- Conversion rate
- Average score
- Score distribution (hot/warm/cold)
- Recent activity (new leads, conversions)
- Quick actions (upload, analytics, CRM)

**Connections**:

- Uses api.analytics.getDashboard()
- Linked to other pages via React Router
- Updates on data changes

---

#### 5. LeadsList.jsx - Lead Management

**Purpose**: Display and manage leads with filtering, sorting, and actions.

**State**:

- `leads`: Array of lead objects
- `loading`: Boolean
- `error`: String
- `total`: Total lead count
- `page`: Current page number
- `pageSize`: Items per page (20)
- `showUploadModal`: Boolean
- `showFilters`: Boolean
- `searchTerm`: String
- `filters`: Object with filter values

**Key Functions**:

##### `loadLeads()`

- **Purpose**: Load leads with current filters and pagination
- **Process**:
  1. Builds params object with filters
  2. Removes empty filter values
  3. Calls api.leads.getLeads(params)
  4. Updates state with results
- **Called by**: useEffect, filter changes, page changes

##### `useEffect` (page, filters dependency)

- **Purpose**: Reload leads when page or filters change
- **Effect**: Runs whenever page or filters change

##### `handleFilterChange(key, value)`

- **Purpose**: Update single filter
- **Process**: Updates filters state, resets page to 1
- **Called by**: Filter select inputs

##### `handleSearch(e)`

- **Purpose**: Handle search form submission
- **Process**: Prevents default, reloads leads
- **Note**: Search not fully implemented in backend

##### `handleDelete(leadId)`

- **Purpose**: Delete lead
- **Process**:
  1. Confirms with user
  2. Calls api.leads.deleteLead(leadId)
  3. Reloads leads
- **Called by**: Delete button

##### `handleMarkConverted(leadId)`

- **Purpose**: Mark lead as converted
- **Process**:
  1. Calls api.leads.markConverted(leadId)
  2. Reloads leads
- **Called by**: Convert button

##### `handleExport(format)`

- **Purpose**: Export leads to file
- **Process**:
  1. Calls api.leads.exportLeads({format, filters})
  2. Creates blob URL
  3. Triggers download
- **Called by**: Export button

**Sub-components**:

##### LeadRow

- **Purpose**: Display single lead in table
- **Props**: lead, onDelete, onMarkConverted
- **Renders**: Lead info, score badge, status, action buttons
- **Icons**: Flame (hot), Zap (warm), Snowflake (cold)

##### FilterSelect

- **Purpose**: Filter dropdown
- **Props**: label, value, onChange, options
- **Renders**: Label + select input

##### UploadModal

- **Purpose**: Upload modal for CSV/JSON
- **Props**: onClose, onSuccess
- **State**: file, uploadType, uploading, error, result
- **Functions**:
  - `handleFileChange(e)`: Handle file selection
  - `handleUpload()`: Upload file via API
- **Renders**: File type selection, file input, upload button, results

**Features**:

- Pagination (previous/next)
- Filtering (source, campaign, status, score category, company size, converted)
- Sorting (score, date, name, company)
- Search (placeholder)
- Export (CSV)
- Upload (CSV/JSON modal)
- Delete, edit, mark converted actions

**Connections**:

- Uses api.leads.\* for all operations
- Filters data server-side
- Reloads on changes

---

#### 6. Analytics.jsx - Analytics Dashboard

**Purpose**: Display comprehensive analytics and charts.

**State**:

- `analytics`: Dashboard data
- `sourcePerformance`: Source performance data
- `campaignPerformance`: Campaign performance data
- `trends`: Trend data
- `loading`: Boolean
- `error`: String
- `trendDays`: Number of days (7/30/90)

**Key Functions**:

##### `loadAnalytics()`

- **Purpose**: Load all analytics data
- **Process**:
  1. Calls multiple API endpoints in parallel (Promise.all)
  2. Gets dashboard, source performance, campaign performance, trends
  3. Updates all state variables
- **Called by**: useEffect, refresh button

##### `useEffect` (trendDays dependency)

- **Purpose**: Reload analytics when trend days change
- **Effect**: Runs when trendDays changes

**Charts Used** (recharts library):

##### Score Distribution Pie Chart

- **Data**: hot/warm/cold counts
- **Shows**: Percentage distribution
- **Colors**: red (hot), yellow (warm), blue (cold)

##### Score Ranges Bar Chart

- **Data**: Score ranges (0-20, 21-40, 41-60, 61-80, 81-100)
- **Shows**: Count of leads in each range

##### Source Performance Bar Chart

- **Data**: Total leads and conversions by source
- **Shows**: Performance comparison
- **Legend**: Total Leads (blue), Conversions (green)

##### Campaign Performance Bar Chart

- **Data**: Total leads and conversions by campaign
- **Shows**: Performance comparison
- **Legend**: Total Leads (purple), Conversions (green)

##### Trends Line Chart

- **Data**: Leads, conversions, average score over time
- **Shows**: Multiple metrics on dual Y-axis
- **Lines**: Leads (blue), Conversions (green), Avg Score (yellow)
- **Filters**: Last 7/30/90 days

**Sub-components**:

##### MetricCard

- **Purpose**: Display single metric
- **Props**: title, value, icon, color
- **Renders**: Icon + title + value

##### ActivityItem

- **Purpose**: Display recent activity
- **Props**: activity object
- **Renders**: Icon + activity text + timestamp + score badge

**Data Tables**:

- Source performance table (source, leads, conversions, rate)
- Campaign performance table (campaign, leads, conversions, rate)

**Connections**:

- Uses api.analytics.\* for all data
- Uses recharts for visualizations
- Refreshable with button

---

## API Endpoints Reference

### Authentication Endpoints

#### POST /auth/register

- **Purpose**: Register new user
- **Request Body**: {username, email}
- **Response**: {user: {id, username, email, api_key, created_at}, access_token}
- **Authentication**: None

#### POST /auth/login

- **Purpose**: Login user
- **Request Body**: FormData {username, password}
- **Response**: {access_token, token_type: "bearer", user: {...}}
- **Authentication**: None

#### GET /auth/me

- **Purpose**: Get current user
- **Response**: {id, username, email, api_key, is_active, created_at}
- **Authentication**: Required (API key or JWT)

#### POST /auth/regenerate-api-key

- **Purpose**: Regenerate API key
- **Response**: {api_key: "new_key"}
- **Authentication**: Required

---

### Lead Endpoints

#### POST /leads/

- **Purpose**: Create new lead
- **Request Body**: LeadCreate schema
- **Response**: LeadResponse schema
- **Side Effects**: Auto-scores lead, sends notification if score ≥ 80
- **Authentication**: Required

#### GET /leads/

- **Purpose**: List leads with filters
- **Query Params**: source, campaign, status, score_min, score_max, score_category, company_size, industry, converted, page, page_size, sort_by, sort_order
- **Response**: {leads: [...], total: int, page: int, page_size: int}
- **Authentication**: Required

#### GET /leads/{id}

- **Purpose**: Get specific lead
- **Response**: LeadResponse schema
- **Authentication**: Required

#### PUT /leads/{id}

- **Purpose**: Update lead
- **Request Body**: LeadUpdate schema
- **Response**: LeadResponse schema
- **Side Effects**: Re-scores if scoring-relevant fields changed
- **Authentication**: Required

#### DELETE /leads/{id}

- **Purpose**: Delete lead
- **Response**: 204 No Content
- **Authentication**: Required

#### POST /leads/bulk

- **Purpose**: Bulk upload leads
- **Request Body**: {leads: [lead_objects]}
- **Response**: {success_count, failed_count, leads: [...], errors: [...]}
- **Side Effects**: Scores all leads, sends notifications for high-priority
- **Authentication**: Required

#### POST /leads/upload/csv

- **Purpose**: Upload CSV file
- **Request Body**: FormData {file}
- **Required Columns**: name, email
- **Response**: {success_count, failed_count, leads: [...], errors: [...]}
- **Side Effects**: Scores all leads, sends notifications for high-priority
- **Authentication**: Required

#### POST /leads/upload/json

- **Purpose**: Upload JSON file
- **Request Body**: FormData {file}
- **Format**: Array of lead objects
- **Response**: {success_count, failed_count, leads: [...], errors: [...]}
- **Side Effects**: Scores all leads, sends notifications for high-priority
- **Authentication**: Required

#### POST /leads/export

- **Purpose**: Export leads
- **Request Body**: {format: "csv"|"json", filters: {...}}
- **Response**: File download (CSV or JSON)
- **Authentication**: Required

#### POST /leads/{id}/mark-converted

- **Purpose**: Mark lead as converted
- **Response**: LeadResponse schema
- **Side Effects**: Sets converted=True, conversion_date=now, status="converted"
- **Authentication**: Required

#### POST /leads/retrain-model

- **Purpose**: Retrain ML model
- **Response**: {success: true, message: "...", metrics: {...}}
- **Side Effects**: Updates all lead scores with new model
- **Authentication**: Required

---

### Analytics Endpoints

#### GET /analytics/conversion-rate

- **Purpose**: Conversion rate analytics
- **Response**: {total_leads, converted_leads, conversion_rate, by_source: {...}, by_campaign: {...}}
- **Authentication**: Required

#### GET /analytics/score-distribution

- **Purpose**: Score distribution
- **Response**: {hot, warm, cold, average_score, score_ranges: {...}}
- **Authentication**: Required

#### GET /analytics/dashboard

- **Purpose**: Complete dashboard analytics
- **Response**: {conversion_rate: {...}, score_distribution: {...}, recent_activity: [...]}
- **Authentication**: Required

#### GET /analytics/source-performance

- **Purpose**: Performance by source
- **Response**: [{source, total_leads, average_score, converted_leads, conversion_rate}]
- **Sorted**: By conversion_rate descending
- **Authentication**: Required

#### GET /analytics/campaign-performance

- **Purpose**: Performance by campaign
- **Response**: [{campaign, total_leads, average_score, converted_leads, conversion_rate}]
- **Sorted**: By conversion_rate descending
- **Authentication**: Required

#### GET /analytics/trends

- **Purpose**: Lead trends over time
- **Query Params**: days (default 30)
- **Response**: [{date, leads, conversions, average_score}]
- **Authentication**: Required

#### GET /analytics/notifications-summary

- **Purpose**: Notifications summary
- **Response**: {total_notifications, by_type: {email, slack}, success_rate, recent_notifications: [...]}
- **Authentication**: Required

---

### Integration Endpoints

#### GET /integrations/config

- **Purpose**: Get integration configuration
- **Response**: {hubspot_api_key, pipedrive_api_key, hubspot_enabled, pipedrive_enabled}
- **Authentication**: Required

#### POST /integrations/sync/hubspot

- **Purpose**: Sync leads to HubSpot
- **Request Body**: {lead_ids: [int], sync_all: boolean}
- **Response**: {success, synced_count, failed_count, errors: [...]}
- **Authentication**: Required

#### POST /integrations/sync/pipedrive

- **Purpose**: Sync leads to Pipedrive
- **Request Body**: {lead_ids: [int], sync_all: boolean}
- **Response**: {success, synced_count, failed_count, errors: [...]}
- **Authentication**: Required

#### POST /integrations/sync/{lead_id}/hubspot

- **Purpose**: Sync single lead to HubSpot
- **Response**: {success: true, message: "...", hubspot_id}
- **Authentication**: Required

#### POST /integrations/sync/{lead_id}/pipedrive

- **Purpose**: Sync single lead to Pipedrive
- **Response**: {success: true, message: "...", pipedrive_id}
- **Authentication**: Required

#### GET /integrations/logs

- **Purpose**: Get integration logs
- **Query Params**: integration_type, limit (default 50)
- **Response**: [{id, lead_id, integration_type, action, external_id, status, error_message, created_at}]
- **Authentication**: Required

#### GET /integrations/status

- **Purpose**: Get integration status
- **Response**: {hubspot: {...}, pipedrive: {...}, total_leads, recent_syncs: [...]}
- **Authentication**: Required

---

## Data Flow & Component Interactions

### 1. User Registration/Login Flow

```
User → Login Component
  ↓
Submit Form → api.auth.login() or api.auth.register()
  ↓
Backend: routers/auth.py
  ↓
Backend: auth.py (authenticate_user or create_user)
  ↓
Backend: models.py (User model)
  ↓
Return user data + tokens
  ↓
Frontend: Store in localStorage
  ↓
App.jsx: Update user state
  ↓
Redirect to Dashboard
```

**Key Functions Involved**:

- Frontend: `authAPI.login()`, `authAPI.register()`
- Backend: `authenticate_user()`, `create_user()`, `verify_password()`, `get_password_hash()`

---

### 2. Lead Creation Flow

```
User → LeadsList Component → Upload Modal
  ↓
Submit Upload → api.leads.uploadCSV() or uploadJSON()
  ↓
Backend: routers/leads.py → upload_csv() or upload_json()
  ↓
Backend: scoring.py → score_leads()
  ↓
  1. _prepare_features() - Convert to ML features
  2. predict() - Score using ML model or heuristic
  3. _get_score_category() - Categorize as hot/warm/cold
  ↓
Backend: models.py → Create Lead record with score
  ↓
Backend: notifications.py → send_lead_notification() if score ≥ 80
  ↓
Backend: models.py → Create NotificationLog record
  ↓
Return results to frontend
  ↓
Frontend: Update leads state, display success
```

**Key Functions Involved**:

- Frontend: `leadsAPI.uploadCSV()`, `leadsAPI.uploadJSON()`
- Backend: `upload_csv()`, `upload_json()`, `score_leads()`, `predict()`, `_prepare_features()`, `send_lead_notification()`

---

### 3. Lead List & Filtering Flow

```
User → LeadsList Component
  ↓
Component Mount → loadLeads()
  ↓
api.leads.getLeads(params)
  ↓
Backend: routers/leads.py → list_leads()
  ↓
  1. Build query with user filter
  2. Apply filters (source, campaign, status, score_category, etc.)
  3. Apply sorting (sort_by, sort_order)
  4. Apply pagination (offset/limit)
  ↓
Backend: models.py → Query Lead table
  ↓
Return {leads, total, page, page_size}
  ↓
Frontend: Update state, render table
  ↓
User interacts (filter, sort, paginate)
  ↓
loadLeads() called again with new params
```

**Key Functions Involved**:

- Frontend: `leadsAPI.getLeads()`, `handleFilterChange()`, `loadLeads()`
- Backend: `list_leads()` (SQLAlchemy query building)

---

### 4. Dashboard Analytics Flow

```
User → Dashboard Component
  ↓
Component Mount → loadDashboard()
  ↓
api.analytics.getDashboard()
  ↓
Backend: routers/analytics.py → get_dashboard_analytics()
  ↓
  1. Call get_conversion_rate()
  2. Call get_score_distribution()
  3. Get recent activity (last 7 days)
  ↓
Backend: SQL Aggregations
  - func.count(), func.avg(), func.sum()
  - GROUP BY queries
  - Date range filtering
  ↓
Return comprehensive analytics
  ↓
Frontend: Update state, render cards and charts
  ↓
Display metrics, score distribution, recent activity
```

**Key Functions Involved**:

- Frontend: `analyticsAPI.getDashboard()`, `loadDashboard()`
- Backend: `get_dashboard_analytics()`, `get_conversion_rate()`, `get_score_distribution()`

---

### 5. Detailed Analytics Flow

```
User → Analytics Component
  ↓
Component Mount → loadAnalytics()
  ↓
Promise.all([
  api.analytics.getDashboard(),
  api.analytics.getSourcePerformance(),
  api.analytics.getCampaignPerformance(),
  api.analytics.getTrends(trendDays)
])
  ↓
Backend: Multiple endpoints called in parallel
  ↓
  1. /analytics/dashboard - Overview data
  2. /analytics/source-performance - Per-source metrics
  3. /analytics/campaign-performance - Per-campaign metrics
  4. /analytics/trends - Time-series data
  ↓
Backend: SQL queries with aggregations and grouping
  ↓
Return all analytics data
  ↓
Frontend: Update all state variables
  ↓
Render multiple charts (recharts)
  - Pie chart: Score distribution
  - Bar charts: Source/campaign performance
  - Line chart: Trends over time
  - Tables: Detailed metrics
```

**Key Functions Involved**:

- Frontend: `analyticsAPI.*` methods, `loadAnalytics()`
- Backend: All analytics endpoint handlers, SQLAlchemy aggregations

---

### 6. Lead Scoring Flow (ML Model)

```
Lead Created/Updated → scoring_engine.predict(leads)
  ↓
  1. Check if model is trained (is_trained flag)
  ↓
  2a. If trained:
      - _prepare_features(leads)
      - scaler.transform(features)
      - model.predict_proba(features)
      - Return probabilities
  ↓
  2b. If not trained (heuristic):
      - _heuristic_score(leads)
      - Calculate score using weighted formula
      - Return scores
  ↓
  3. Add score, conversion_probability, score_category to leads
  ↓
  4. _get_score_category(score)
     - hot: ≥80
     - warm: 50-79
     - cold: <50
  ↓
Return scored leads
```

**Feature Engineering**:

- Source, campaign, medium weights
- Company size, budget weights
- Email domain quality (corporate vs free)
- Engagement metrics (interactions, pages visited, time on site)
- Recency score (based on last interaction date)

**Key Functions Involved**:

- `predict()`, `_prepare_features()`, `_heuristic_score()`, `_get_score_category()`, `_get_email_domain_quality()`, `_calculate_recency_score()`

---

### 7. Notification Flow

```
Lead Created/Updated → Check if score ≥ 80
  ↓
If yes → notifications.send_lead_notification(lead, db)
  ↓
  1. Compose email message
  2. Compose Slack message
  ↓
  2a. Email notification:
      - Use SMTP settings from .env
      - Send via smtplib
  ↓
  2b. Slack notification:
      - Use SLACK_WEBHOOK_URL from .env
      - POST to webhook
  ↓
  3. Create NotificationLog record
     - Log notification type, recipient, status
  ↓
Return notification result
```

**Key Functions Involved**:

- `send_lead_notification()`, `send_email_notification()`, `send_slack_notification()`

---

### 8. CRM Integration Flow

```
User → Integrations Component
  ↓
Click "Sync to HubSpot/Pipedrive"
  ↓
api.integrations.syncToHubSpot() or syncToPipedrive()
  ↓
Backend: routers/integrations.py → sync_to_hubspot_crm()
  ↓
  1. Get leads to sync (all or specific IDs)
  2. Call integrations.bulk_sync_to_hubspot(leads, db)
  ↓
Backend: integrations.py → bulk_sync_to_hubspot()
  ↓
  For each lead:
    1. Check if already synced (has hubspot_id)
    2. If yes: Update existing contact
    3. If no: Create new contact
    4. Store hubspot_id in lead record
    5. Create IntegrationLog record
  ↓
Return sync results
  ↓
Frontend: Display success/error message
```

**Key Functions Involved**:

- Frontend: `integrationsAPI.syncToHubSpot()`, `integrationsAPI.syncToPipedrive()`
- Backend: `sync_to_hubspot_crm()`, `sync_to_pipedrive_crm()`, `bulk_sync_to_hubspot()`, `bulk_sync_to_pipedrive()`, `sync_to_hubspot()`, `sync_to_pipedrive()`

---

### 9. Model Retraining Flow

```
User → Click "Retrain Model" button
  ↓
api.leads.retrainModel()
  ↓
Backend: routers/leads.py → retrain_scoring_model()
  ↓
Backend: scoring.py → scoring_engine.retrain(db)
  ↓
  1. Query all leads with conversion status
  2. Validate minimum requirements (10 leads, 2+ in each class)
  3. Prepare lead dictionaries and labels (0/1)
  4. Call train(leads, labels)
     - _prepare_features()
     - train_test_split()
     - scaler.fit_transform()
     - LogisticRegression.fit()
     - Evaluate accuracy
     - _save_model()
  5. Predict scores for all leads
  6. Update all lead scores in database
  7. Commit changes
  ↓
Return training metrics
  ↓
Frontend: Display success message
```

**Key Functions Involved**:

- Frontend: `leadsAPI.retrainModel()`
- Backend: `retrain_scoring_model()`, `retrain()`, `train()`, `_save_model()`

---

### 10. Authentication Flow for API Requests

```
Frontend Component → api.apiRequest(endpoint, options)
  ↓
  1. Get API key from localStorage
  2. Get auth token from localStorage
  3. Add headers:
     - X-API-Key: {api_key} (if present)
     - Authorization: Bearer {token} (if no API key)
  ↓
Fetch request to backend
  ↓
Backend: Depends on get_current_user()
  ↓
  1. Try API key authentication:
     - get_current_user_by_api_key()
     - Query User by api_key
  2. Try JWT token authentication:
     - get_current_user_by_token()
     - verify_token()
     - Query User by username
  ↓
If successful: Return User object
If failed: Throw 401 Unauthorized
  ↓
Router endpoint uses User object for operations
  - Filters queries by user_id
  - Enforces ownership/permissions
```

**Key Functions Involved**:

- Frontend: `apiRequest()`
- Backend: `get_current_user()`, `get_current_user_by_api_key()`, `get_current_user_by_token()`, `verify_token()`

---

## Function Reference

### Backend Function Quick Reference

#### scoring.py Functions

| Function                           | Purpose                      | Returns                        |
| ---------------------------------- | ---------------------------- | ------------------------------ |
| `LeadScoringEngine.__init__()`     | Initialize scoring engine    | None                           |
| `_prepare_features(leads)`         | Convert leads to ML features | DataFrame                      |
| `_get_email_domain_quality(email)` | Score email domain           | Float (0.8 or 0.5)             |
| `_calculate_recency_score(date)`   | Calculate recency score      | Float (0.2-1.0)                |
| `train(leads, labels)`             | Train ML model               | {accuracy, feature_importance} |
| `predict(leads)`                   | Score leads                  | List of scored leads           |
| `_heuristic_score(leads)`          | Fallback scoring             | List of scored leads           |
| `_get_score_category(score)`       | Categorize score             | "hot"/"warm"/"cold"            |
| `retrain(db)`                      | Retrain with database data   | Training metrics               |
| `_save_model()`                    | Save model to disk           | None                           |
| `_load_model()`                    | Load model from disk         | None                           |
| `_initialize_default_model()`      | Create default model         | None                           |

#### auth.py Functions

| Function                                     | Purpose              | Returns           |
| -------------------------------------------- | -------------------- | ----------------- |
| `verify_password(plain, hashed)`             | Verify password      | Boolean           |
| `get_password_hash(password)`                | Hash password        | Hashed string     |
| `generate_api_key()`                         | Generate API key     | "lsk\_..." string |
| `create_access_token(data, delta)`           | Create JWT token     | Token string      |
| `verify_token(token)`                        | Decode JWT token     | Payload or None   |
| `get_current_user_by_api_key()`              | Auth via API key     | User object       |
| `get_current_user_by_token()`                | Auth via JWT token   | User object       |
| `get_current_user()`                         | Auth via either      | User object       |
| `create_user(db, username, email, password)` | Create user          | User object       |
| `authenticate_user(db, username, password)`  | Validate credentials | User or None      |
| `verify_admin_key(api_key)`                  | Check admin key      | Boolean           |

#### notifications.py Functions

| Function                                  | Purpose                 | Returns     |
| ----------------------------------------- | ----------------------- | ----------- |
| `send_lead_notification(lead, db)`        | Send notifications      | Dict result |
| `send_email_notification(lead)`           | Send email              | Dict result |
| `send_slack_notification(lead)`           | Send Slack message      | Dict result |
| `send_bulk_lead_notifications(leads, db)` | Send bulk notifications | None        |

#### integrations.py Functions

| Function                            | Purpose                | Returns                        |
| ----------------------------------- | ---------------------- | ------------------------------ |
| `sync_to_hubspot(lead, db)`         | Sync to HubSpot        | {success, error, hubspot_id}   |
| `sync_to_pipedrive(lead, db)`       | Sync to Pipedrive      | {success, error, pipedrive_id} |
| `bulk_sync_to_hubspot(leads, db)`   | Bulk sync to HubSpot   | {success, failed, errors}      |
| `bulk_sync_to_pipedrive(leads, db)` | Bulk sync to Pipedrive | {success, failed, errors}      |

### Frontend Function Quick Reference

#### api.js Functions

| Function                                   | Purpose               | Endpoint                               |
| ------------------------------------------ | --------------------- | -------------------------------------- |
| `api.auth.register(username, email)`       | Register user         | POST /auth/register                    |
| `api.auth.login(username, password)`       | Login user            | POST /auth/login                       |
| `api.auth.getCurrentUser()`                | Get current user      | GET /auth/me                           |
| `api.auth.regenerateApiKey()`              | Regenerate API key    | POST /auth/regenerate-api-key          |
| `api.auth.logout()`                        | Logout                | (localStorage)                         |
| `api.leads.getLeads(params)`               | List leads            | GET /leads/                            |
| `api.leads.getLead(leadId)`                | Get lead              | GET /leads/{id}                        |
| `api.leads.createLead(data)`               | Create lead           | POST /leads/                           |
| `api.leads.updateLead(leadId, data)`       | Update lead           | PUT /leads/{id}                        |
| `api.leads.deleteLead(leadId)`             | Delete lead           | DELETE /leads/{id}                     |
| `api.leads.bulkUpload(leads)`              | Bulk upload           | POST /leads/bulk                       |
| `api.leads.uploadCSV(file)`                | Upload CSV            | POST /leads/upload/csv                 |
| `api.leads.uploadJSON(file)`               | Upload JSON           | POST /leads/upload/json                |
| `api.leads.exportLeads(req)`               | Export leads          | POST /leads/export                     |
| `api.leads.markConverted(leadId)`          | Mark converted        | POST /leads/{id}/mark-converted        |
| `api.leads.retrainModel()`                 | Retrain model         | POST /leads/retrain-model              |
| `api.analytics.getConversionRate()`        | Conversion rate       | GET /analytics/conversion-rate         |
| `api.analytics.getScoreDistribution()`     | Score distribution    | GET /analytics/score-distribution      |
| `api.analytics.getDashboard()`             | Dashboard data        | GET /analytics/dashboard               |
| `api.analytics.getSourcePerformance()`     | Source performance    | GET /analytics/source-performance      |
| `api.analytics.getCampaignPerformance()`   | Campaign performance  | GET /analytics/campaign-performance    |
| `api.analytics.getTrends(days)`            | Trends                | GET /analytics/trends                  |
| `api.analytics.getNotificationsSummary()`  | Notifications summary | GET /analytics/notifications-summary   |
| `api.integrations.getConfig()`             | Get config            | GET /integrations/config               |
| `api.integrations.syncToHubSpot(req)`      | Sync to HubSpot       | POST /integrations/sync/hubspot        |
| `api.integrations.syncToPipedrive(req)`    | Sync to Pipedrive     | POST /integrations/sync/pipedrive      |
| `api.integrations.syncLeadToHubSpot(id)`   | Sync single lead      | POST /integrations/sync/{id}/hubspot   |
| `api.integrations.syncLeadToPipedrive(id)` | Sync single lead      | POST /integrations/sync/{id}/pipedrive |
| `api.integrations.getLogs(params)`         | Get logs              | GET /integrations/logs                 |
| `api.integrations.getStatus()`             | Get status            | GET /integrations/status               |

---

## Summary

The Lead Scoring Engine is a well-architected full-stack application with clear separation of concerns:

### Backend (Python/FastAPI)

- **Main.py**: Application entry point and routing
- **Database.py**: SQLite connection management
- **Models.py**: SQLAlchemy ORM models (User, Lead, NotificationLog, IntegrationLog)
- **Auth.py**: JWT and API key authentication
- **Scoring.py**: ML-based lead scoring (Logistic Regression)
- **Notifications.py**: Email and Slack notifications
- **Integrations.py**: HubSpot and Pipedrive CRM sync
- **Routers/**: Organized API endpoints by feature

### Frontend (React)

- **App.jsx**: Routing and authentication state
- **api.js**: Centralized API client with authentication
- **Login.jsx**: User authentication UI
- **Dashboard.jsx**: Overview with metrics and quick actions
- **LeadsList.jsx**: Lead management with filtering and pagination
- **Analytics.jsx**: Comprehensive analytics with charts
- **Integrations.jsx**: CRM configuration and sync

### Key Features

1. **Automatic Lead Scoring**: ML model scores leads on creation/update
2. **Bulk Operations**: CSV/JSON upload with automatic scoring
3. **Analytics Dashboard**: Conversion rates, score distribution, trends
4. **Notifications**: Email/Slack for high-priority leads (score ≥ 80)
5. **CRM Integration**: HubSpot and Pipedrive sync
6. **Export**: CSV/JSON export with filters
7. **Model Retraining**: Retrain ML model as conversion data accumulates

### Data Flow

1. User actions → Frontend components → API service layer
2. API requests → FastAPI routers → Business logic
3. Business logic → Database operations → Response
4. Response → Frontend state updates → UI rendering

The system uses dependency injection, proper error handling, and follows RESTful API principles throughout.
