# Lead Scoring Engine - Testing Guide

## Current Status: ✅ READY FOR TESTING

Both servers are running:

- **Backend API**: http://localhost:8000
- **Frontend App**: http://localhost:5173

---

## Quick Start Testing

### 1. Access the Application

Open your browser and navigate to: **http://localhost:5173**

### 2. Login / Register

#### Option A: Register a New Account

1. Click "Don't have an account? Create one"
2. Fill in:
   - **Username**: Your desired username (e.g., "testuser")
   - **Email**: Your email (e.g., "test@example.com")
   - **Password**: Create a password (or leave blank for MVP mode)
3. Click "Create Account"
4. You'll be automatically logged in

#### Option B: Login with Existing Account

1. Enter your **Username**
2. Enter your **Password** (or use username as password for MVP mode)
3. Click "Sign In"

---

## Page-by-Page Testing

### 📊 Dashboard Page

**URL**: http://localhost:5173/dashboard

**What to Test**:

- [ ] Page loads without errors
- [ ] Stats cards show correct numbers (Total Leads, Converted, Conversion Rate, Avg Score)
- [ ] Score Distribution shows Hot/Warm/Cold counts
- [ ] Recent Activity displays recent leads
- [ ] Quick Action buttons navigate to correct pages

**Expected Behavior**:

- If no leads exist, shows "No recent activity"
- Stats display 0 or actual counts based on data

---

### 👥 Leads Page

**URL**: http://localhost:5173/leads

**What to Test**:

#### View Leads

- [ ] Page loads and displays leads table
- [ ] If no leads, shows "No leads found" message
- [ ] Each lead shows: Name, Email, Company, Source, Score, Status
- [ ] Score badges display correctly (Hot/Warm/Cold)

#### Upload Leads (CSV)

1. Click "Upload" button
2. Select "CSV" file type
3. Use the sample file: `sample-leads.csv` (in project root)
4. Click "Upload"
5. [ ] Success message appears with count
6. [ ] Leads appear in table after refresh

#### Upload Leads (JSON)

1. Click "Upload" button
2. Select "JSON" file type
3. Use the sample file: `sample-leads.json` (in project root)
4. Click "Upload"
5. [ ] Success message appears with count

#### Filter Leads

1. Click "Filters" button
2. Try different filters:
   - [ ] Source (website, referral, paid_ads, etc.)
   - [ ] Campaign (awareness, consideration, decision, retention)
   - [ ] Status (new, contacted, qualified, converted, lost)
   - [ ] Score Category (hot, warm, cold)
   - [ ] Sort By (Score, Date Created, Name, Company)
   - [ ] Sort Order (Ascending, Descending)
3. [ ] Results update correctly

#### Search Leads

1. Type in search box
2. [ ] Press Enter or wait (search implementation may be basic)

#### Lead Actions

- [ ] **Mark as Converted**: Click target icon on a lead
- [ ] **Delete Lead**: Click trash icon (with confirmation)
- [ ] **Edit Lead**: Click edit icon (may open modal or navigate)

#### Pagination

- [ ] "Previous" and "Next" buttons work
- [ ] Page indicator shows correct page

#### Export Leads

1. Click "Export" button
2. [ ] CSV file downloads with current leads
3. [ ] File contains all lead data

---

### 📈 Analytics Page

**URL**: http://localhost:5173/analytics

**What to Test**:

#### Key Metrics

- [ ] Total Leads count matches
- [ ] Conversions count matches
- [ ] Conversion Rate percentage displays
- [ ] Average Score displays

#### Score Distribution Chart

- [ ] Pie chart renders correctly
- [ ] Shows Hot/Warm/Cold breakdown
- [ ] Legend displays correctly

#### Score Ranges Chart

- [ ] Bar chart shows score ranges (0-20, 21-40, etc.)
- [ ] Hover tooltips work

#### Source Performance

- [ ] Bar chart shows leads by source
- [ ] Table below shows detailed breakdown
- [ ] Conversion rates calculate correctly

#### Campaign Performance

- [ ] Bar chart shows leads by campaign
- [ ] Table below shows detailed breakdown

#### Lead Trends

- [ ] Line chart shows trends over time
- [ ] Date selector works (7 days, 30 days, 90 days)
- [ ] Multiple lines: Leads, Conversions, Avg Score

#### Recent Activity

- [ ] Activity list displays
- [ ] Shows lead names and timestamps

#### Refresh

- [ ] Click "Refresh" button
- [ ] Data reloads with latest information

---

### 🔌 Integrations Page

**URL**: http://localhost:5173/integrations

**What to Test**:

#### Integration Cards

- [ ] HubSpot card displays
- [ ] Pipedrive card displays
- [ ] Shows "Connected" or "Not configured" status
- [ ] Shows synced/unsynced lead counts

#### Configuration Info

- [ ] Instructions display for setting up API keys
- [ ] Environment variable names are correct

#### Sync Functionality

**Note**: Requires API keys in `backend/.env`

1. Add to `backend/.env`:
   ```
   HUBSPOT_API_KEY=your-hubspot-api-key
   PIPEDRIVE_API_KEY=your-pipedrive-api-key
   ```
2. Restart backend server
3. [ ] "Connected" status appears
4. [ ] "Sync New" button works
5. [ ] "Sync All" button works
6. [ ] Success message shows synced count

#### Sync History

- [ ] Logs display recent sync activity
- [ ] Shows integration type, action, status
- [ ] Timestamps display correctly

---

## API Testing (Optional)

### Using Swagger UI

1. Navigate to: **http://localhost:8000/docs**
2. Test endpoints directly:
   - [ ] POST /auth/register - Register new user
   - [ ] POST /auth/login - Login user
   - [ ] GET /auth/me - Get current user
   - [ ] GET /leads/ - List leads
   - [ ] POST /leads/ - Create lead
   - [ ] POST /leads/upload/csv - Upload CSV
   - [ ] GET /analytics/dashboard - Get analytics
   - [ ] GET /integrations/config - Get integration config

---

## Sample Data Files

### sample-leads.csv

Located in project root. Contains 10 sample leads with various scores.

### sample-leads.json

Located in project root. Contains same leads in JSON format.

---

## Common Issues & Solutions

### Issue: "Login failed"

**Solution**:

- Ensure username is correct
- For MVP, try using username as password
- Check browser console for errors (F12)

### Issue: "Failed to load leads"

**Solution**:

- Check backend server is running (http://localhost:8000)
- Check browser console for CORS errors
- Verify you're logged in

### Issue: "Upload failed"

**Solution**:

- Ensure CSV has required columns: name, email
- Check file format is valid
- Check backend logs for errors

### Issue: Charts not displaying

**Solution**:

- Ensure you have leads in the database
- Refresh the page
- Check browser console for errors

### Issue: Integrations show "Not configured"

**Solution**:

- Add API keys to `backend/.env`
- Restart backend server
- Check API keys are valid

---

## Backend Server Commands

### Start Backend

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Stop Backend

Press `Ctrl+C` in the backend terminal

---

## Frontend Server Commands

### Start Frontend

```bash
cd frontend
npm run dev
```

### Stop Frontend

Press `Ctrl+C` in the frontend terminal

---

## Database Management

### View Database

The SQLite database is at: `backend/leads.db`

You can view it using:

- DB Browser for SQLite (https://sqlitebrowser.org/)
- Or any SQLite viewer

### Reset Database

1. Stop backend server
2. Delete `backend/leads.db`
3. Restart backend server (it will recreate the database)

---

## Environment Variables

### Backend (.env)

```
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
DATABASE_URL=sqlite:///./leads.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
HUBSPOT_API_KEY=
PIPEDRIVE_API_KEY=
```

### Frontend (.env)

```
VITE_API_URL=http://localhost:8000
```

---

## Testing Checklist

### Authentication

- [ ] Register new user
- [ ] Login with credentials
- [ ] Logout works
- [ ] Session persists on refresh

### Dashboard

- [ ] Page loads correctly
- [ ] Stats display accurately
- [ ] Recent activity shows

### Leads Management

- [ ] View all leads
- [ ] Upload CSV file
- [ ] Upload JSON file
- [ ] Filter leads
- [ ] Sort leads
- [ ] Search leads
- [ ] Mark lead as converted
- [ ] Delete lead
- [ ] Export leads

### Analytics

- [ ] View all charts
- [ ] Score distribution displays
- [ ] Source performance shows
- [ ] Campaign performance shows
- [ ] Trends display
- [ ] Refresh works

### Integrations

- [ ] View integration status
- [ ] View sync history
- [ ] (Optional) Configure API keys
- [ ] (Optional) Test sync

---

## Success Criteria

The project is fully functional when:

✅ You can register/login to the application
✅ Dashboard displays lead statistics
✅ You can upload leads from CSV/JSON files
✅ Leads are automatically scored (0-100)
✅ You can view, filter, and sort leads
✅ Analytics charts display correctly
✅ You can export leads to CSV
✅ Integrations page loads and shows status
✅ All pages navigate correctly
✅ No console errors in browser
✅ Backend API responds correctly

---

## Next Steps After Testing

1. **If everything works**: The project is complete! 🎉
2. **If issues found**: Document them and report
3. **For production**:
   - Change SECRET_KEY in .env
   - Use a production database (PostgreSQL)
   - Set up proper error logging
   - Add rate limiting
   - Implement proper user roles/permissions

---

## Support

If you encounter issues:

1. Check browser console (F12) for JavaScript errors
2. Check backend terminal for Python errors
3. Verify both servers are running
4. Check network tab in browser dev tools for failed requests

---

**Last Updated**: 2026-01-03
**Version**: 1.0.0
