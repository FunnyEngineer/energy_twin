"""
ML Algorithm for Energy Twin Similarity Matching
Uses scikit-learn to find the k most similar homes based on ResStock features
REDESIGNED to work with native ResStock data structure
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import NearestNeighbors
import pickle
import os


class EnergyTwinMatcher:
    """Machine Learning model for finding similar homes using native ResStock features"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.model = None
        
        # Use ResStock's native column names for features
        # NOTE: monthly_kwh is NOT included - we find similar homes by characteristics,
        # then predict energy usage from those similar homes
        self.numeric_features = [
            'in.sqft..ft2',
            'in.bedrooms',
            'in.occupants',
        ]
        
        self.categorical_features = [
            'in.geometry_building_type_acs',
            'in.heating_fuel',
            'in.hvac_cooling_type',
            'in.ashrae_iecc_climate_zone_2004',
        ]
        
    def preprocess_data(self, df, fit=True):
        """
        Preprocess home data using ResStock's native structure
        NO transformation - just encoding and scaling
        """
        df = df.copy()
        
        # Handle missing numeric values with median
        for col in self.numeric_features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if fit:
                    median_val = df[col].median()
                    if pd.isna(median_val):
                        median_val = 1500 if col == 'in.sqft..ft2' else 2
                    df[col].fillna(median_val, inplace=True)
                else:
                    # Use pre-fitted median (stored in scaler mean)
                    df[col].fillna(df[col].median(), inplace=True)
        
        # Encode categorical variables
        for col in self.categorical_features:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown').astype(str)
                
                if fit:
                    self.label_encoders[col] = LabelEncoder()
                    df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
                else:
                    if col in self.label_encoders:
                        # Handle unseen categories
                        try:
                            df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
                        except ValueError:
                            # If category not seen during training, use most common
                            df[f'{col}_encoded'] = 0
                    else:
                        df[f'{col}_encoded'] = 0
        
        # Solar encoding (boolean to int)
        if 'has_solar_panel' in df.columns:
            df['has_solar_encoded'] = df['has_solar_panel'].astype(int)
        elif 'in.has_pv' in df.columns:
            df['has_solar_encoded'] = (df['in.has_pv'] == 'Yes').astype(int)
        else:
            df['has_solar_encoded'] = 0
        
        # Combine features
        feature_cols = (
            self.numeric_features +
            [f'{col}_encoded' for col in self.categorical_features if col in df.columns] +
            ['has_solar_encoded']
        )
        
        # Select only available columns
        available_cols = [col for col in feature_cols if col in df.columns]
        features = df[available_cols].values
        
        # Scale features
        if fit:
            features_scaled = self.scaler.fit_transform(features)
        else:
            features_scaled = self.scaler.transform(features)
            
        return features_scaled
    
    def fit(self, homes_data):
        """Train the model on ResStock homes data"""
        # homes_data can be DataFrame or list of dicts
        if isinstance(homes_data, list):
            df = pd.DataFrame(homes_data)
        else:
            df = homes_data.copy()
        
        # Preprocess the data
        X = self.preprocess_data(df, fit=True)
        
        # Use k-NN for finding similar homes
        n_neighbors = min(50, len(df))  # Use more neighbors for better results
        self.model = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean', algorithm='auto')
        self.model.fit(X)
        
        print(f"   🤖 ML model trained on {len(df):,} homes with {X.shape[1]} features")
        
        return self
    
    def find_similar_homes(self, user_home, homes_data, k=10):
        """
        Find k most similar homes to the user's home
        Works with ResStock native format
        """
        # Convert user home to DataFrame with ResStock column names
        user_df = pd.DataFrame([user_home])
        
        # Preprocess user data
        user_features = self.preprocess_data(user_df, fit=False)
        
        # Convert homes_data to DataFrame and preprocess
        if isinstance(homes_data, list):
            homes_df = pd.DataFrame(homes_data)
        else:
            homes_df = homes_data.copy()
            
        homes_features = self.preprocess_data(homes_df, fit=False)
        
        # Find k nearest neighbors
        k_actual = min(k, len(homes_data))
        distances, indices = self.model.kneighbors(user_features, n_neighbors=k_actual)
        
        # Calculate similarity scores (convert distance to similarity)
        # Using inverse distance: similarity = 1 / (1 + distance)
        similarities = 1 / (1 + distances[0])
        
        # Get the similar homes - return as dictionaries
        similar_homes = []
        for idx, similarity in zip(indices[0], similarities):
            if isinstance(homes_data, list):
                home = homes_data[idx].copy()
            else:
                home = homes_df.iloc[idx].to_dict()
            home['similarity_score'] = float(similarity)
            similar_homes.append(home)
        
        return similar_homes
    
    def predict_energy_usage(self, user_home, homes_data, k=50):
        """
        Predict energy usage based on similar homes' characteristics
        Does NOT use monthly_kwh as input feature
        """
        # Find similar homes (without using energy usage as feature)
        similar_homes = self.find_similar_homes(user_home, homes_data, k=k)
        
        # Extract their actual energy usage
        usages = []
        for home in similar_homes:
            usage = home.get('monthly_kwh', home.get('monthly_usage'))
            if usage:
                usages.append(float(usage))
        
        if not usages:
            return 900.0  # Fallback
        
        # Weighted average based on similarity scores
        weights = [h.get('similarity_score', 1.0) for h in similar_homes[:len(usages)]]
        predicted_usage = np.average(usages, weights=weights)
        
        return float(predicted_usage)
    
    def calculate_insights(self, similar_homes, user_home):
        """
        Calculate insights from similar homes using ResStock data
        """
        # Extract monthly usage from similar homes
        usages = []
        for h in similar_homes:
            usage = h.get('monthly_kwh', h.get('monthly_usage', 900))
            usages.append(float(usage))
        
        # Extract heating types (native ResStock format)
        heating_types = [h.get('in.heating_fuel', 'Unknown') for h in similar_homes]
        
        insights = {
            'avg_twin_usage': float(np.mean(usages)),
            'min_usage': float(np.min(usages)),
            'max_usage': float(np.max(usages)),
            'common_heating': max(set(heating_types), key=heating_types.count) if heating_types else 'Unknown',
            'recommendation': self._generate_recommendation(user_home, similar_homes, usages)
        }
        
        return insights
    
    def _generate_recommendation(self, user_home, similar_homes, usages):
        """Generate personalized recommendation based on ResStock data"""
        avg_usage = np.mean(usages)
        
        # Check if user provided their usage
        user_usage = user_home.get('monthly_kwh', user_home.get('monthly_usage'))
        
        if user_usage:
            user_usage = float(user_usage)
            if user_usage > avg_usage * 1.2:
                return f"Your energy usage ({int(user_usage)} kWh/month) is higher than similar homes (avg: {int(avg_usage)} kWh/month). Consider energy-efficient upgrades."
            elif user_usage < avg_usage * 0.8:
                return f"Excellent! Your energy usage ({int(user_usage)} kWh/month) is lower than similar homes (avg: {int(avg_usage)} kWh/month)."
            else:
                return f"Your energy usage ({int(user_usage)} kWh/month) is typical for similar homes (avg: {int(avg_usage)} kWh/month)."
        else:
            return f"Based on {len(similar_homes)} similar homes in ResStock, you can expect around {int(avg_usage)} kWh/month."
    
    def save_model(self, filepath):
        """Save the trained model"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath):
        """Load a trained model"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.label_encoders = model_data['label_encoders']
            return True
        return False
