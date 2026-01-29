"""
ML Algorithm for Energy Twin Similarity Matching
Uses scikit-learn to find the k most similar homes based on various features
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os


class EnergyTwinMatcher:
    """Machine Learning model for finding similar homes based on energy profiles"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.model = None
        self.feature_columns = [
            'home_size', 'bedrooms', 'occupants', 'monthly_usage',
            'temperature', 'home_type_encoded', 'heating_type_encoded',
            'cooling_type_encoded', 'has_solar_encoded'
        ]
        
    def preprocess_data(self, df, fit=True):
        """Preprocess home data for ML model"""
        df = df.copy()
        
        # Encode categorical variables
        categorical_columns = ['home_type', 'heating_type', 'cooling_type']
        
        for col in categorical_columns:
            if fit:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                if col in self.label_encoders:
                    df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
                else:
                    df[f'{col}_encoded'] = 0
        
        # Encode binary solar column
        if 'has_solar' in df.columns:
            df['has_solar_encoded'] = df['has_solar'].astype(int)
        
        # Select feature columns
        features = df[self.feature_columns].values
        
        # Scale features
        if fit:
            features_scaled = self.scaler.fit_transform(features)
        else:
            features_scaled = self.scaler.transform(features)
            
        return features_scaled
    
    def fit(self, homes_data):
        """Train the model on existing homes data"""
        df = pd.DataFrame(homes_data)
        
        # Preprocess the data
        X = self.preprocess_data(df, fit=True)
        
        # Use k-NN for finding similar homes
        self.model = NearestNeighbors(n_neighbors=20, metric='euclidean', algorithm='auto')
        self.model.fit(X)
        
        return self
    
    def find_similar_homes(self, user_home, homes_data, k=10):
        """Find k most similar homes to the user's home"""
        
        # Convert user home to DataFrame
        user_df = pd.DataFrame([user_home])
        
        # Preprocess user data
        user_features = self.preprocess_data(user_df, fit=False)
        
        # Convert homes_data to DataFrame and preprocess
        homes_df = pd.DataFrame(homes_data)
        homes_features = self.preprocess_data(homes_df, fit=False)
        
        # Find k nearest neighbors
        distances, indices = self.model.kneighbors(user_features, n_neighbors=min(k, len(homes_data)))
        
        # Calculate similarity scores (convert distance to similarity)
        # Using inverse distance: similarity = 1 / (1 + distance)
        similarities = 1 / (1 + distances[0])
        
        # Get the similar homes
        similar_homes = []
        for idx, similarity in zip(indices[0], similarities):
            home = homes_data[idx].copy()
            home['similarity_score'] = float(similarity)
            similar_homes.append(home)
        
        return similar_homes
    
    def calculate_insights(self, similar_homes, user_home):
        """Calculate insights from similar homes"""
        
        usages = [h['monthly_usage'] for h in similar_homes]
        heating_types = [h['heating_type'] for h in similar_homes]
        
        insights = {
            'avg_twin_usage': np.mean(usages),
            'min_usage': np.min(usages),
            'max_usage': np.max(usages),
            'common_heating': max(set(heating_types), key=heating_types.count),
            'recommendation': self._generate_recommendation(user_home, similar_homes)
        }
        
        return insights
    
    def _generate_recommendation(self, user_home, similar_homes):
        """Generate personalized recommendation"""
        avg_usage = np.mean([h['monthly_usage'] for h in similar_homes])
        
        if user_home.get('monthly_usage'):
            user_usage = float(user_home['monthly_usage'])
            if user_usage > avg_usage * 1.2:
                return "Your energy usage is higher than similar homes. Consider energy-efficient upgrades like LED lighting, better insulation, or a programmable thermostat."
            elif user_usage < avg_usage * 0.8:
                return "Great job! Your energy usage is lower than similar homes. You're already doing well with energy efficiency."
            else:
                return "Your energy usage is on par with similar homes. Small changes like adjusting thermostat settings can lead to savings."
        else:
            return f"Based on homes similar to yours, you can expect around {int(avg_usage)} kWh/month. Installing solar panels could reduce your energy costs significantly."
    
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
