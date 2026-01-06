# Frontend Setup Guide

This guide will help you set up and run the Lead Scoring Engine frontend.

## Prerequisites

- Node.js 16 or higher
- npm or yarn package manager

## Installation Steps

### 1. Navigate to the Frontend Directory

```bash
cd lead-scoring-engine/frontend
```

### 2. Install Dependencies

```bash
npm install
```

or if you use yarn:

```bash
yarn install
```

### 3. Configure Environment Variables (Optional)

Create a `.env` file in the frontend directory (optional, as defaults are provided):

```env
VITE_API_URL=http://localhost:8000
```

If your backend is running on a different host or port, update this value.

### 4. Start Development Server

```bash
npm run dev
```

or with yarn:

```bash
yarn dev
```

The application will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Project Structure

```
frontend/
├── public/           # Static assets
├── src/
│   ├── components/   # React components
│   │   ├── Analytics.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Header.jsx
│   │   ├── Integrations.jsx
│   │   ├── LeadsList.jsx
│   │   └── Login.jsx
│   ├── services/     # API service layer
│   │   └── api.js
│   ├── App.jsx       # Main app component
│   ├── main.jsx      # Entry point
│   └── index.css     # Global styles
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## Features

### Dashboard

- Overview of total leads, conversions, and conversion rate
- Score distribution (hot/warm/cold)
- Recent activity feed
- Quick actions

### Leads Management

- List all leads with pagination
- Filter by source, campaign, status, score category, etc.
- Sort by score, date, name, or company
- Upload leads via CSV or JSON
- Export leads to CSV or JSON
- Mark leads as converted
- Delete leads

### Analytics

- Conversion rate metrics
- Score distribution charts
- Performance by source and campaign
- Lead trends over time
- Recent activity

### Integrations

- Configure HubSpot integration
- Configure Pipedrive integration
- Sync leads to CRM
- View sync history

## Sample Data

### CSV Format

Create a CSV file with the following columns:

```csv
name,email,company,phone,title,source,campaign,medium,past_interactions,pages_visited,time_on_site,company_size,industry,budget,notes,tags
John Doe,john@example.com,Acme Corp,+1234567890,CTO,website,awareness,organic,5,15,10.5,medium,Technology,medium,Important lead,enterprise,vip
Jane Smith,jane@example.com,Startup Inc,,CEO,referral,decision,referral,3,8,5.2,small,SaaS,high,Hot prospect,decision-maker
```

### Required Columns

- `name` - Lead's full name
- `email` - Lead's email address

### Optional Columns

- `company` - Company name
- `phone` - Phone number
- `title` - Job title
- `source` - Lead source (website, referral, paid_ads, etc.)
- `campaign` - Campaign name
- `medium` - Marketing medium (organic, cpc, email, etc.)
- `past_interactions` - Number of past interactions
- `pages_visited` - Number of pages visited on website
- `time_on_site` - Time spent on site in minutes
- `company_size` - Company size (startup, small, medium, large, enterprise)
- `industry` - Industry
- `budget` - Budget level (low, medium, high, enterprise)
- `notes` - Additional notes
- `tags` - Comma-separated tags

### JSON Format

```json
[
  {
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Corp",
    "source": "website",
    "campaign": "awareness",
    "past_interactions": 5,
    "company_size": "medium",
    "budget": "high"
  },
  {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "company": "Startup Inc",
    "source": "referral",
    "campaign": "decision",
    "past_interactions": 3,
    "company_size": "small",
    "budget": "medium"
  }
]
```

## Troubleshooting

### Port Already in Use

If port 5173 is already in use, you can change it in `vite.config.js`:

```javascript
server: {
  port: 3000,
  // ...
}
```

### API Connection Errors

If you see API connection errors:

1. Make sure the backend server is running on `http://localhost:8000`
2. Check CORS settings in backend `.env` file
3. Verify API URL in frontend `.env` file

### Build Errors

If you encounter build errors:

```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```

## Production Build

To build for production:

```bash
npm run build
```

The built files will be in the `dist` directory. You can preview the build:

```bash
npm run preview
```

## Deployment

### Static Hosting

The frontend can be deployed to any static hosting service:

- Vercel
- Netlify
- GitHub Pages
- AWS S3 + CloudFront

### Environment Variables for Production

Set the production API URL:

```env
VITE_API_URL=https://your-api-domain.com
```

Then build and deploy:

```bash
npm run build
```

## Browser Support

The application supports all modern browsers:

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Tips

### Hot Module Replacement

The development server supports hot module replacement (HMR). Changes to components will be reflected immediately without a full page reload.

### React DevTools

Install React DevTools browser extension for better debugging:

- Chrome: https://chrome.google.com/webstore/detail/react-developer-tools
- Firefox: https://addons.mozilla.org/en-US/firefox/addon/react-devtools

### API Testing

You can test the API directly using the Swagger UI at `http://localhost:8000/docs` while developing.
