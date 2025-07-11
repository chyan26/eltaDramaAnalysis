import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set English font to avoid Chinese character issues
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

def create_visualizations_english():
    """Create rating analysis visualizations with English labels"""
    
    print("Loading data...")
    # Read cleaned data
    df = pd.read_csv('integrated_program_ratings_cleaned.csv')
    df = df[df['Rating'].notna()]
    df['Date'] = pd.to_datetime(df['Date'])
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
    
    print("Creating charts...")
    # Create charts
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Elta TV Rating Analysis Dashboard', fontsize=18, fontweight='bold', y=0.98)
    
    # 1. Hourly ratings analysis
    print("  Generating hourly analysis chart...")
    hourly_ratings = df.groupby('Hour')['Rating'].mean()
    bars = axes[0, 0].bar(hourly_ratings.index, hourly_ratings.values, 
                         color='skyblue', alpha=0.8, edgecolor='navy', linewidth=0.5)
    axes[0, 0].set_title('Average Rating by Hour', fontsize=14, pad=20)
    axes[0, 0].set_xlabel('Hour of Day', fontsize=12)
    axes[0, 0].set_ylabel('Average Rating', fontsize=12)
    axes[0, 0].set_xticks(range(0, 24, 2))
    axes[0, 0].grid(True, alpha=0.3)
    
    # Add value labels for high bars
    for bar in bars:
        height = bar.get_height()
        if height > 0.15:  # Only show values for higher bars
            axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + 0.005,
                           f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 2. Monthly rating trends
    print("  Generating monthly trend chart...")
    monthly_ratings = df.groupby(df['Date'].dt.month)['Rating'].mean()
    axes[0, 1].plot(monthly_ratings.index, monthly_ratings.values, 
                   marker='o', linewidth=3, markersize=8, color='darkgreen')
    axes[0, 1].set_title('Monthly Rating Trends', fontsize=14, pad=20)
    axes[0, 1].set_xlabel('Month', fontsize=12)
    axes[0, 1].set_ylabel('Average Rating', fontsize=12)
    axes[0, 1].set_xticks(range(1, 13))
    axes[0, 1].grid(True, alpha=0.3)
    
    # Add value labels
    for i, v in enumerate(monthly_ratings.values):
        axes[0, 1].text(i+1, v + 0.002, f'{v:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 3. Top series rating comparison
    print("  Generating series comparison chart...")
    series_counts = df['Cleaned_Series_Name'].value_counts()
    major_series = series_counts[series_counts >= 50].head(8)  # Series with 50+ episodes
    series_ratings = []
    series_names_en = []
    
    # Create English mapping for major series
    series_mapping = {
        '蠟筆小新': 'Crayon Shin-chan',
        '延禧攻略': 'Story of Yanxi Palace',
        '後宮甄嬛傳': 'Empresses in the Palace',
        '墨雨雲間': 'The Double',
        '那年花開月正圓': 'Nothing But Thirty',
        '琅琊榜': 'Nirvana in Fire',
        '神鵰俠侶': 'The Return of the Condor Heroes',
        '月升滄海': 'Till the End of the Moon'
    }
    
    for series in major_series.index:
        avg_rating = df[df['Cleaned_Series_Name'] == series]['Rating'].mean()
        series_ratings.append(avg_rating)
        # Use English name if available, otherwise shorten Chinese name
        eng_name = series_mapping.get(series, series[:8] + '...' if len(series) > 8 else series)
        series_names_en.append(eng_name)
    
    bars = axes[1, 0].barh(series_names_en, series_ratings, 
                          color='lightcoral', alpha=0.8, edgecolor='darkred', linewidth=0.5)
    axes[1, 0].set_title('Top Series Average Ratings', fontsize=14, pad=20)
    axes[1, 0].set_xlabel('Average Rating', fontsize=12)
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        axes[1, 0].text(width + 0.005, bar.get_y() + bar.get_height()/2,
                       f'{width:.3f}', ha='left', va='center', fontsize=10)
    
    # 4. Rating distribution
    print("  Generating rating distribution chart...")
    n, bins, patches = axes[1, 1].hist(df['Rating'], bins=25, color='lightgreen', 
                                      alpha=0.7, edgecolor='darkgreen', linewidth=0.5)
    axes[1, 1].set_title('Rating Distribution', fontsize=14, pad=20)
    axes[1, 1].set_xlabel('Rating', fontsize=12)
    axes[1, 1].set_ylabel('Number of Programs', fontsize=12)
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add statistics text
    mean_rating = df['Rating'].mean()
    max_rating = df['Rating'].max()
    axes[1, 1].axvline(mean_rating, color='red', linestyle='--', alpha=0.7, linewidth=2)
    axes[1, 1].text(0.7, 0.9, f'Mean: {mean_rating:.3f}\\nMax: {max_rating:.3f}', 
                   transform=axes[1, 1].transAxes, fontsize=11, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    
    # Save chart
    print("Saving chart...")
    plt.savefig('ratings_analysis_english.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # Show chart
    plt.show()
    
    print("✓ Visualization chart saved as 'ratings_analysis_english.png'")
    
    # Output statistics
    print("\\nChart Statistics:")
    print(f"- Total programs: {len(df):,}")
    print(f"- Average rating: {df['Rating'].mean():.4f}")
    print(f"- Maximum rating: {df['Rating'].max():.4f}")
    print(f"- Major series count: {len(major_series)}")
    print(f"- Prime time (8-10 PM) avg rating: {df[df['Hour'].between(20, 22)]['Rating'].mean():.4f}")

if __name__ == "__main__":
    create_visualizations_english()
