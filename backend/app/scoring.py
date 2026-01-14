"""
AI Lead Scoring Engine
Uses machine learning to predict lead conversion probability
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeadScoringEngine:
    """
    Machine learning-based lead scoring engine
    Uses Logistic Regression for predicting conversion probability
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the scoring engine
        
        Args:
            model_path: Path to saved model file (optional)
        """
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.is_trained = False
        self.model_path = model_path or "models/lead_scoring_model.pkl"
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path) if os.path.dirname(self.model_path) else ".", exist_ok=True)
        
        # Try to load existing model
        self._load_model()
    
    def _get_numeric(self, value, default=0.0) -> float:
        """
        Safely convert a value to float
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Float value
        """
        if value is None:
            return default
        
        # Handle pandas/numpy NaN
        if isinstance(value, float) and np.isnan(value):
            return default
            
        # Handle lists/sequences
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) > 0:
                return self._get_numeric(value[0], default)
            return default
            
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _prepare_features(self, leads: List[Dict]) -> pd.DataFrame:
        """
        Prepare features for ML model from lead data
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            DataFrame with prepared features
        """
        # Clean lead data before creating DataFrame
        cleaned_leads = []
        for lead in leads:
            cleaned_lead = {}
            for key, value in lead.items():
                # Handle lists/sequences by taking first element or converting to string
                if isinstance(value, (list, tuple)):
                    cleaned_lead[key] = str(value[0]) if len(value) > 0 else ''
                else:
                    cleaned_lead[key] = value
            cleaned_leads.append(cleaned_lead)
        
        df = pd.DataFrame(cleaned_leads)
        
        # Convert numeric columns to proper numeric types (preserve floats for time_on_site)
        numeric_cols = ['past_interactions', 'pages_visited', 'time_on_site']
        for col in numeric_cols:
            if col in df.columns:
                # Convert to numeric, handling strings and invalid values
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                # Ensure past_interactions and pages_visited are integers
                if col in ['past_interactions', 'pages_visited']:
                    df[col] = df[col].astype(int)
                # Ensure time_on_site is float
                elif col == 'time_on_site':
                    df[col] = df[col].astype(float)
                # Ensure no NaN values remain
                df[col] = df[col].fillna(0)
        
        # Define feature mappings (adjusted for better score distribution)
        source_weights = {
            'website': 0.5,
            'referral': 0.7,
            'paid_ads': 0.4,
            'social_media': 0.3,
            'email': 0.6,
            'cold_call': 0.2,
            'event': 0.5,
            'partner': 0.6,
            None: 0.4
        }
        
        campaign_weights = {
            'awareness': 0.3,
            'consideration': 0.5,
            'decision': 0.7,
            'retention': 0.4,
            None: 0.4
        }
        
        medium_weights = {
            'organic': 0.6,
            'cpc': 0.4,
            'cpm': 0.3,
            'email': 0.5,
            'referral': 0.7,
            'direct': 0.5,
            None: 0.4
        }
        
        company_size_weights = {
            'startup': 0.4,
            'small': 0.5,
            'medium': 0.6,
            'large': 0.7,
            'enterprise': 0.8,
            None: 0.4
        }
        
        budget_weights = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.7,
            'enterprise': 0.9,
            None: 0.4
        }
        
        # Create engineered features
        df['source_score'] = df['source'].map(source_weights).fillna(0.5)
        df['campaign_score'] = df['campaign'].map(campaign_weights).fillna(0.5)
        df['medium_score'] = df['medium'].map(medium_weights).fillna(0.5)
        df['company_size_score'] = df['company_size'].map(company_size_weights).fillna(0.5)
        df['budget_score'] = df['budget'].map(budget_weights).fillna(0.5)
        
        # Email domain quality (simple heuristic)
        df['email_domain_quality'] = df['email'].apply(self._get_email_domain_quality)
        
        # Engagement features (reduced multipliers)
        df['interaction_score'] = df['past_interactions'].fillna(0) * 0.06
        df['engagement_score'] = (
            df['pages_visited'].fillna(0) * 0.03 +
            df['time_on_site'].fillna(0) * 0.015
        )
        
        # Recency score (more recent = higher score)
        if 'last_interaction_date' in df.columns:
            df['recency_score'] = df['last_interaction_date'].apply(
                lambda x: self._calculate_recency_score(x) if pd.notna(x) else 0.5
            )
        else:
            df['recency_score'] = 0.5
        
        # Select feature columns
        self.feature_columns = [
            'source_score',
            'campaign_score',
            'medium_score',
            'company_size_score',
            'budget_score',
            'email_domain_quality',
            'interaction_score',
            'engagement_score',
            'recency_score'
        ]
        
        # Fill missing values
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.5
            df[col] = df[col].fillna(0.5)
        
        return df[self.feature_columns]
    
    def _get_email_domain_quality(self, email: str) -> float:
        """
        Calculate email domain quality score
        
        Args:
            email: Email address
            
        Returns:
            Quality score (0-1)
        """
        if not email or '@' not in email:
            return 0.3
        
        domain = email.split('@')[1].lower()
        
        # Premium domains
        premium_domains = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com']
        
        # Corporate domains (not free email providers)
        if domain not in premium_domains:
            return 0.8
        
        return 0.5
    
    def _calculate_recency_score(self, date: datetime) -> float:
        """
        Calculate recency score based on last interaction date
        
        Args:
            date: Last interaction date
            
        Returns:
            Recency score (0-1)
        """
        if not date:
            return 0.3
        
        now = datetime.now()
        days_ago = (now - date).days
        
        if days_ago <= 1:
            return 1.0
        elif days_ago <= 7:
            return 0.8
        elif days_ago <= 30:
            return 0.6
        elif days_ago <= 90:
            return 0.4
        else:
            return 0.2
    
    def train(self, leads: List[Dict], labels: List[int]) -> Dict:
        """
        Train the lead scoring model
        
        Args:
            leads: List of lead dictionaries
            labels: List of conversion labels (0 or 1)
            
        Returns:
            Training metrics
        """
        logger.info(f"Training model with {len(leads)} leads")
        
        # Prepare features
        X = self._prepare_features(leads)
        y = np.array(labels)
        
        # Check if we have enough data for stratification
        unique_classes = len(np.unique(y))
        min_class_count = min(np.bincount(y))
        
        # Only use stratify if we have at least 2 samples in each class
        use_stratify = unique_classes >= 2 and min_class_count >= 2
        
        if use_stratify:
            logger.info(f"Using stratified split with {unique_classes} classes")
        else:
            logger.warning(f"Insufficient data for stratification (min class count: {min_class_count}). Using random split.")
        
        # Split data
        if use_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.is_trained = True
        
        # Save model
        self._save_model()
        
        logger.info(f"Model trained with accuracy: {accuracy:.2f}")
        
        return {
            'accuracy': accuracy,
            'feature_importance': dict(zip(self.feature_columns, self.model.coef_[0]))
        }
    
    def predict(self, leads: List[Dict]) -> List[Dict]:
        """
        Predict conversion probability for leads
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of leads with scores
        """
        if not self.is_trained:
            # If model not trained, use heuristic scoring
            return self._heuristic_score(leads)
        
        # Prepare features
        X = self._prepare_features(leads)
        X_scaled = self.scaler.transform(X)
        
        # Predict probabilities
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        # Add scores to leads
        scored_leads = []
        for lead, prob in zip(leads, probabilities):
            score = prob * 100
            scored_lead = lead.copy()
            scored_lead['score'] = round(score, 2)
            scored_lead['conversion_probability'] = round(prob, 4)
            scored_lead['score_category'] = self._get_score_category(score)
            
            # Add explanation, confidence, and recommendation
            scored_lead['explanation'] = self._calculate_score_explanation(lead, score)
            confidence_data = self._calculate_confidence(lead)
            scored_lead.update(confidence_data)
            scored_lead['recommendation'] = self._get_recommendation(score, lead)
            
            # Add missing data alerts (Phase 2)
            scored_lead['missing_data'] = self._identify_missing_data(lead)
            
            scored_leads.append(scored_lead)
        
        return scored_leads
    
    def _heuristic_score(self, leads: List[Dict]) -> List[Dict]:
        """
        Fallback heuristic scoring when model is not trained
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of leads with heuristic scores
        """
        scored_leads = []
        
        for lead in leads:
            score = 30.0  # Lower base score for better distribution
            
            # Source bonus (adjusted weights)
            source_weights = {
                'referral': 15,
                'website': 8,
                'email': 10,
                'paid_ads': 3,
                'social_media': 3,
                'event': 8,
                'partner': 12,
                'cold_call': 0
            }
            score += source_weights.get(lead.get('source'), 0)
            
            # Engagement bonus (reduced multipliers)
            past_interactions = self._get_numeric(lead.get('past_interactions'))
            pages_visited = self._get_numeric(lead.get('pages_visited'))
            time_on_site = self._get_numeric(lead.get('time_on_site'))
            
            score += min(past_interactions * 3, 15)
            score += min(pages_visited * 1.5, 8)
            score += min(time_on_site * 0.3, 4)
            
            # Company size bonus (reduced weights)
            company_weights = {
                'enterprise': 12,
                'large': 8,
                'medium': 4,
                'small': 0,
                'startup': -3
            }
            score += company_weights.get(lead.get('company_size'), 0)
            
            # Budget bonus (reduced weights)
            budget_weights = {
                'enterprise': 12,
                'high': 8,
                'medium': 4,
                'low': -3
            }
            score += budget_weights.get(lead.get('budget'), 0)
            
            # Email domain bonus (reduced)
            email = lead.get('email', '')
            if email and '@' in email:
                domain = email.split('@')[1].lower()
                if domain not in ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com']:
                    score += 8
            
            # Campaign bonus (new factor)
            campaign_weights = {
                'decision': 10,
                'consideration': 6,
                'retention': 4,
                'awareness': 2
            }
            score += campaign_weights.get(lead.get('campaign'), 0)
            
            # Medium bonus (new factor)
            medium_weights = {
                'referral': 8,
                'organic': 5,
                'direct': 4,
                'email': 5,
                'cpc': 3,
                'cpm': 2
            }
            score += medium_weights.get(lead.get('medium'), 0)
            
            # Clamp score to 0-100
            score = max(0, min(100, score))
            
            scored_lead = lead.copy()
            scored_lead['score'] = round(score, 2)
            scored_lead['conversion_probability'] = round(score / 100, 4)
            scored_lead['score_category'] = self._get_score_category(score)
            
            # Add explanation, confidence, and recommendation
            scored_lead['explanation'] = self._calculate_score_explanation(lead, score)
            confidence_data = self._calculate_confidence(lead)
            scored_lead.update(confidence_data)
            scored_lead['recommendation'] = self._get_recommendation(score, lead)
            
            # Add missing data alerts (Phase 2)
            scored_lead['missing_data'] = self._identify_missing_data(lead)
            
            scored_leads.append(scored_lead)
        
        return scored_leads
    
    def _calculate_score_explanation(self, lead: Dict, score: float, base_score: float = 30.0) -> Dict:
        """
        Calculate detailed score breakdown showing factor contributions
        
        Args:
            lead: Lead dictionary
            score: Final calculated score
            base_score: Starting base score
            
        Returns:
            Dictionary with score explanation
        """
        factors = []
        
        # Source contribution
        source_weights = {
            'referral': 15, 'website': 8, 'email': 10, 'paid_ads': 3,
            'social_media': 3, 'event': 8, 'partner': 12, 'cold_call': 0
        }
        source = lead.get('source')
        if source and source in source_weights:
            contrib = source_weights[source]
            if contrib != 0:
                factors.append({
                    "factor": f"{source.replace('_', ' ').title()} source",
                    "contribution": contrib,
                    "category": "source"
                })
        
        # Campaign contribution
        campaign_weights = {'decision': 10, 'consideration': 6, 'retention': 4, 'awareness': 2}
        campaign = lead.get('campaign')
        if campaign and campaign in campaign_weights:
            contrib = campaign_weights[campaign]
            factors.append({
                "factor": f"{campaign.title()}-stage campaign",
                "contribution": contrib,
                "category": "campaign"
            })
        
        # Engagement contributions
        past_interactions = self._get_numeric(lead.get('past_interactions'))
        if past_interactions > 0:
            contrib = min(past_interactions * 3, 15)
            factors.append({
                "factor": f"High engagement ({int(past_interactions)} interactions)",
                "contribution": round(contrib, 1),
                "category": "engagement"
            })
        
        pages_visited = self._get_numeric(lead.get('pages_visited'))
        if pages_visited > 0:
            contrib = min(pages_visited * 1.5, 8)
            factors.append({
                "factor": f"Website activity ({int(pages_visited)} pages)",
                "contribution": round(contrib, 1),
                "category": "engagement"
            })
        
        time_on_site = self._get_numeric(lead.get('time_on_site'))
        if time_on_site > 0:
            contrib = min(time_on_site * 0.3, 4)
            factors.append({
                "factor": f"Time on site ({time_on_site:.1f} min)",
                "contribution": round(contrib, 1),
                "category": "engagement"
            })
        
        # Company size contribution
        company_weights = {'enterprise': 12, 'large': 8, 'medium': 4, 'small': 0, 'startup': -3}
        company_size = lead.get('company_size')
        if company_size and company_size in company_weights:
            contrib = company_weights[company_size]
            if contrib != 0:
                factors.append({
                    "factor": f"{company_size.title()} company",
                    "contribution": contrib,
                    "category": "company_fit"
                })
        
        # Budget contribution
        budget_weights = {'enterprise': 12, 'high': 8, 'medium': 4, 'low': -3}
        budget = lead.get('budget')
        if budget and budget in budget_weights:
            contrib = budget_weights[budget]
            if contrib != 0:
                factors.append({
                    "factor": f"{budget.title()} budget",
                    "contribution": contrib,
                    "category": "company_fit"
                })
        
        # Email domain quality
        email = lead.get('email', '')
        if email and '@' in email:
            domain = email.split('@')[1].lower()
            if domain not in ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com']:
                factors.append({
                    "factor": "Corporate email domain",
                    "contribution": 8,
                    "category": "quality"
                })
        
        # Medium contribution
        medium_weights = {'referral': 8, 'organic': 5, 'direct': 4, 'email': 5, 'cpc': 3, 'cpm': 2}
        medium = lead.get('medium')
        if medium and medium in medium_weights:
            contrib = medium_weights[medium]
            if contrib > 0:
                factors.append({
                    "factor": f"{medium.upper() if medium == 'cpc' or medium == 'cpm' else medium.title()} traffic",
                    "contribution": contrib,
                    "category": "source"
                })
        
        # Sort by absolute contribution
        factors.sort(key=lambda x: abs(x['contribution']), reverse=True)
        
        # Calculate percentages
        total_contrib = sum(abs(f['contribution']) for f in factors)
        for factor in factors:
            if total_contrib > 0:
                factor['percentage'] = f"{abs(factor['contribution']) / total_contrib * 100:.0f}%"
            else:
                factor['percentage'] = "0%"
        
        positive_factors = [f for f in factors if f['contribution'] > 0][:3]
        negative_factors = [f for f in factors if f['contribution'] < 0][:3]
        
        return {
            "top_positive_factors": positive_factors,
            "top_negative_factors": negative_factors,
            "base_score": base_score,
            "all_factors": factors
        }
    
    def _calculate_confidence(self, lead: Dict) -> Dict:
        """
        Calculate confidence level based on available data
        
        Args:
            lead: Lead dictionary
            
        Returns:
            Dictionary with confidence score and level
        """
        # Count available data points (9 total factors)
        data_points = sum([
            1 if lead.get('source') else 0,
            1 if lead.get('campaign') else 0,
            1 if lead.get('medium') else 0,
            1 if self._get_numeric(lead.get('past_interactions')) > 0 else 0,
            1 if self._get_numeric(lead.get('pages_visited')) > 0 else 0,
            1 if self._get_numeric(lead.get('time_on_site')) > 0 else 0,
            1 if lead.get('company_size') else 0,
            1 if lead.get('budget') else 0,
            1 if lead.get('email') and '@' in lead.get('email') else 0
        ])
        
        confidence_score = data_points / 9.0
        
        if confidence_score >= 0.75:
            confidence_level = 'high'
            confidence_label = 'High Confidence'
        elif confidence_score >= 0.5:
            confidence_level = 'medium'
            confidence_label = 'Medium Confidence'
        else:
            confidence_level = 'low'
            confidence_label = 'Low Confidence'
        
        return {
            "confidence": round(confidence_score, 2),
            "confidence_level": confidence_level,
            "confidence_label": confidence_label,
            "data_points": data_points,
            "total_factors": 9
        }
    
    def _get_recommendation(self, score: float, lead: Dict) -> Dict:
        """
        Get actionable recommendation based on score and lead data
        
        Args:
            score: Lead score (0-100)
            lead: Lead dictionary
            
        Returns:
            Dictionary with recommendation details
        """
        if score >= 80:
            return {
                "priority": "urgent",
                "action": "Call within 24 hours",
                "reason": "High conversion probability - immediate follow-up recommended",
                "icon": "🔥",
                "timeline": "Today"
            }
        elif score >= 50:
            return {
                "priority": "medium",
                "action": "Nurture with email sequence",
                "reason": "Good potential - needs engagement and relationship building",
                "icon": "⚡",
                "timeline": "3-5 days"
            }
        else:
            return {
                "priority": "low",
                "action": "Add to drip campaign",
                "reason": "Early-stage lead - focus on education and awareness",
                "icon": "❄️",
                "timeline": "2 weeks"
            }
    
    def _identify_missing_data(self, lead: Dict) -> List[Dict]:
        """
        Identify missing data and calculate potential score improvement
        
        Args:
            lead: Lead dictionary
            
        Returns:
            List of missing fields with impact estimates
        """
        missing_alerts = []
        
        # Check company size
        if not lead.get('company_size'):
            missing_alerts.append({
                "field": "Company Size",
                "potential_impact": "+4 to +12 points",
                "priority": "high",
                "suggestion": "Ask about company size in first call",
                "icon": "🏢"
            })
        
        # Check budget
        if not lead.get('budget'):
            missing_alerts.append({
                "field": "Budget",
                "potential_impact": "+4 to +12 points",
                "priority": "high",
                "suggestion": "Qualify budget during discovery",
                "icon": "💰"
            })
        
        # Check campaign
        if not lead.get('campaign'):
            missing_alerts.append({
                "field": "Campaign Stage",
                "potential_impact": "+2 to +10 points",
                "priority": "medium",
                "suggestion": "Track which campaign stage they're in",
                "icon": "📊"
            })
        
        # Check medium
        if not lead.get('medium'):
            missing_alerts.append({
                "field": "Traffic Medium",
                "potential_impact": "+2 to +8 points",
                "priority": "medium",
                "suggestion": "Track how they found you (organic, referral, etc.)",
                "icon": "🔍"
            })
        
        # Check engagement data
        past_interactions = self._get_numeric(lead.get('past_interactions'))
        pages_visited = self._get_numeric(lead.get('pages_visited'))
        time_on_site = self._get_numeric(lead.get('time_on_site'))
        
        if past_interactions == 0 and pages_visited == 0 and time_on_site == 0:
            missing_alerts.append({
                "field": "Engagement Data",
                "potential_impact": "+0 to +15 points",
                "priority": "medium",
                "suggestion": "Track website visits, email opens, and interactions",
                "icon": "📈"
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        missing_alerts.sort(key=lambda x: priority_order[x["priority"]])
        
        # Return top 3
        return missing_alerts[:3]
    
    def _calculate_comparative_insights(self, lead_score: float, db, user_id: int) -> Optional[Dict]:
        """
        Calculate how this lead compares to others
        
        Args:
            lead_score: Score of current lead
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with comparative insights or None if insufficient data
        """
        from .models import Lead
        
        # Get all user's leads
        all_leads = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.score.isnot(None)
        ).all()
        
        if len(all_leads) < 5:
            return None
        
        # Calculate percentile
        scores = [l.score for l in all_leads]
        scores.sort()
        percentile = (sum(1 for s in scores if s < lead_score) / len(scores)) * 100
        
        # Find similar leads (±5 points)
        similar_leads = [
            l for l in all_leads 
            if abs(l.score - lead_score) <= 5 and l.score != lead_score
        ]
        
        # Calculate conversion rate of similar leads
        similar_converted = sum(1 for l in similar_leads if l.converted)
        similar_conv_rate = (similar_converted / len(similar_leads)) if similar_leads else 0
        
        return {
            "percentile": round(percentile, 0),
            "rank_text": f"Top {100-percentile:.0f}%" if percentile > 50 else f"Bottom {percentile:.0f}%",
            "similar_leads_count": len(similar_leads),
            "similar_converted": similar_converted,
            "similar_conversion_rate": round(similar_conv_rate * 100, 1),
            "total_leads": len(all_leads)
        }
    
    def _calculate_dynamic_thresholds(self, db, user_id: int) -> Dict:
        """
        Calculate personalized Hot/Warm/Cold thresholds based on user's data
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with threshold values and method used
        """
        from .models import Lead
        
        # Get user's leads with conversion data
        leads = db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.score.isnot(None)
        ).all()
        
        if len(leads) < 20:  # Need minimum data
            return {"hot": 80, "warm": 50, "method": "default", "sample_size": len(leads)}
        
        # Group by score ranges and calculate conversion rates
        score_ranges = {}
        for lead in leads:
            range_key = int(lead.score // 10) * 10  # 0-9, 10-19, etc.
            if range_key not in score_ranges:
                score_ranges[range_key] = {"total": 0, "converted": 0}
            score_ranges[range_key]["total"] += 1
            if lead.converted:
                score_ranges[range_key]["converted"] += 1
        
        # Find optimal thresholds
        hot_threshold = 80
        warm_threshold = 50
        
        for score, data in sorted(score_ranges.items(), reverse=True):
            if data["total"] >= 5:
                conv_rate = data["converted"] / data["total"]
                if conv_rate >= 0.4 and score < hot_threshold:
                    hot_threshold = score
                    break
        
        for score, data in sorted(score_ranges.items(), reverse=True):
            if data["total"] >= 5:
                conv_rate = data["converted"] / data["total"]
                if conv_rate >= 0.15 and score < hot_threshold:
                    warm_threshold = score
                    break
        
        return {
            "hot": hot_threshold,
            "warm": warm_threshold,
            "method": "dynamic",
            "sample_size": len(leads)
        }
    
    def enrich_lead(self, lead_dict: Dict, db, user_id: int) -> Dict:
        """
        Enrich lead data with all Phase 1 and 2 scoring enhancements
        
        Args:
            lead_dict: Lead dictionary
            db: Database session
            user_id: User ID
            
        Returns:
            Enriched lead dictionary
        """
        score = lead_dict.get('score', 0)
        
        # Phase 1: Explanation, Confidence, Recommendation
        lead_dict['explanation'] = self._calculate_score_explanation(lead_dict, score)
        confidence_data = self._calculate_confidence(lead_dict)
        lead_dict.update(confidence_data)
        lead_dict['recommendation'] = self._get_recommendation(score, lead_dict)
        
        # Phase 2: Missing Data, Comparative Insights, and Dynamic Thresholds
        lead_dict['missing_data'] = self._identify_missing_data(lead_dict)
        lead_dict['comparative_insights'] = self._calculate_comparative_insights(score, db, user_id)
        
        # Dynamic Thresholds (Phase 2)
        thresholds = self._calculate_dynamic_thresholds(db, user_id)
        lead_dict['thresholds'] = thresholds
        
        # Update category if using dynamic thresholds
        if thresholds['method'] == 'dynamic':
            if score >= thresholds['hot']:
                lead_dict['score_category'] = 'hot'
            elif score >= thresholds['warm']:
                lead_dict['score_category'] = 'warm'
            else:
                lead_dict['score_category'] = 'cold'
        
        return lead_dict
    
    def _get_score_category(self, score: float) -> str:
        """
        Get score category based on score value
        
        Args:
            score: Lead score (0-100)
            
        Returns:
            Category: 'hot', 'warm', or 'cold'
        """
        if score >= 80:
            return 'hot'
        elif score >= 50:
            return 'warm'
        else:
            return 'cold'
    
    def retrain(self, db) -> Dict:
        """
        Retrain the model with all leads from database
        
        Args:
            db: Database session
            
        Returns:
            Training metrics
        """
        from .models import Lead
        
        logger.info("Retraining model with database data")
        
        # Get all leads with conversion status
        leads = db.query(Lead).all()
        
        if len(leads) < 10:
            logger.warning(f"Not enough leads to train model. Found {len(leads)} leads, minimum 10 required. Using heuristic scoring.")
            return {'error': 'Not enough data for training', 'leads_count': len(leads), 'minimum_required': 10}
        
        # Check if we have both converted and non-converted leads
        converted_count = sum(1 for lead in leads if lead.converted)
        non_converted_count = len(leads) - converted_count
        
        if converted_count < 2 or non_converted_count < 2:
            logger.warning(f"Insufficient class distribution for training. Converted: {converted_count}, Non-converted: {non_converted_count}. Need at least 2 in each class.")
            return {'error': 'Insufficient class distribution', 'converted': converted_count, 'non_converted': non_converted_count}
        
        # Prepare data
        lead_dicts = []
        labels = []
        
        for lead in leads:
            lead_dict = {
                'name': lead.name,
                'email': lead.email,
                'company': lead.company,
                'source': lead.source,
                'campaign': lead.campaign,
                'medium': lead.medium,
                'past_interactions': lead.past_interactions,
                'pages_visited': lead.pages_visited,
                'time_on_site': lead.time_on_site,
                'company_size': lead.company_size,
                'budget': lead.budget,
                'last_interaction_date': lead.last_interaction_date
            }
            lead_dicts.append(lead_dict)
            labels.append(1 if lead.converted else 0)
        
        # Train model
        metrics = self.train(lead_dicts, labels)
        
        # Update all lead scores in database
        scored_leads = self.predict(lead_dicts)
        for i, scored_lead in enumerate(scored_leads):
            lead = leads[i]
            lead.score = scored_lead['score']
            lead.score_category = scored_lead['score_category']
            lead.conversion_probability = scored_lead['conversion_probability']
        
        db.commit()
        
        return metrics
    
    def _save_model(self):
        """Save model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {self.model_path}")
    
    def _load_model(self):
        """Load model from disk"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.label_encoders = model_data['label_encoders']
                self.feature_columns = model_data['feature_columns']
                self.is_trained = model_data['is_trained']
                
                logger.info(f"Model loaded from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
                self._initialize_default_model()
        else:
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize a default untrained model"""
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.is_trained = False
        logger.info("Initialized default untrained model")


# Global scoring engine instance
scoring_engine = LeadScoringEngine()


def score_leads(leads: List[Dict]) -> List[Dict]:
    """
    Score a list of leads
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        List of leads with scores
    """
    return scoring_engine.predict(leads)


def retrain_model(db) -> Dict:
    """
    Retrain the scoring model
    
    Args:
        db: Database session
        
    Returns:
        Training metrics
    """
    return scoring_engine.retrain(db)


def enrich_lead_data(lead_obj, db, user_id: int) -> Dict:
    """
    Enrich a lead database object or dictionary with AI insights
    
    Args:
        lead_obj: Lead database model or dictionary
        db: Database session
        user_id: User ID
        
    Returns:
        Enriched lead dictionary
    """
    # Convert DB model to dict if needed
    if hasattr(lead_obj, "__dict__"):
        lead_dict = {
            column.name: getattr(lead_obj, column.name)
            for column in lead_obj.__table__.columns
        }
    else:
        lead_dict = lead_obj.copy()
    
    return scoring_engine.enrich_lead(lead_dict, db, user_id)
