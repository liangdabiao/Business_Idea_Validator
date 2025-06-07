"""
Streamlit UI for Business Idea Validator

This script provides a web-based user interface for the business_validator package,
allowing users to validate business ideas and view the results in an interactive dashboard.
"""

import streamlit as st
import pandas as pd
import json
import os
import time
import glob
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

from business_validator import validate_business_idea
from business_validator.config import DATA_DIR
from business_validator.utils.environment import setup_environment

# Set page configuration
st.set_page_config(
    page_title="Business Idea Validator",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f1f8fe;
        margin-bottom: 1rem;
        text-align: center;
    }
    .insight-text {
        font-size: 1.1rem;
        line-height: 1.5;
    }
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #9e9e9e;
    }
</style>
""", unsafe_allow_html=True)

def load_previous_runs():
    """Load previous validation runs from the data directory."""
    runs = []
    
    # Get all subdirectories in the data directory
    if os.path.exists(DATA_DIR):
        subdirs = [f.path for f in os.scandir(DATA_DIR) if f.is_dir()]
        
        for subdir in subdirs:
            # Check if this is a completed run with a final analysis
            final_analysis_path = os.path.join(subdir, "07_final_analysis.json")
            keywords_path = os.path.join(subdir, "01_keywords.json")
            
            if os.path.exists(final_analysis_path) and os.path.exists(keywords_path):
                # Get run ID from directory name
                run_id = os.path.basename(subdir)
                
                # Load business idea from keywords file
                try:
                    with open(keywords_path, 'r', encoding='utf-8') as f:
                        keywords_data = json.load(f)
                        business_idea = keywords_data.get("business_idea", "Unknown")
                except:
                    business_idea = "Unknown"
                
                # Get timestamp from run_id
                timestamp_str = run_id.split('_')[-2] + '_' + run_id.split('_')[-1]
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    timestamp_display = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    timestamp_display = "Unknown"
                    timestamp = datetime.now()  # Fallback for sorting
                
                # Add to runs list
                runs.append({
                    "run_id": run_id,
                    "business_idea": business_idea,
                    "timestamp": timestamp,
                    "timestamp_display": timestamp_display,
                    "data_dir": subdir,
                    "final_analysis_path": final_analysis_path
                })
    
    # Sort runs by timestamp (newest first)
    runs.sort(key=lambda x: x["timestamp"], reverse=True)
    return runs

def load_analysis_from_file(file_path):
    """Load analysis data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading analysis: {e}")
        return None

def display_validation_results(analysis_data, business_idea):
    """Display validation results in a dashboard format."""
    if not analysis_data:
        st.error("No analysis data available.")
        return
    
    # Extract data
    overall_score = analysis_data.get("overall_score", 0)
    summary = analysis_data.get("market_validation_summary", "No summary available.")
    pain_points = analysis_data.get("key_pain_points", [])
    solutions = analysis_data.get("existing_solutions", [])
    opportunities = analysis_data.get("market_opportunities", [])
    platform_insights = analysis_data.get("platform_insights", [])
    recommendations = analysis_data.get("recommendations", [])
    st.session_state['recommendations'] = recommendations
    
    # Header
    st.markdown(f"<h1 class='main-header'>Validation Results: {business_idea}</h1>", unsafe_allow_html=True)
    
    # Score and Summary
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create gauge chart for overall score
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Validation Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1E88E5"},
                'steps': [
                    {'range': [0, 30], 'color': "#EF5350"},
                    {'range': [30, 50], 'color': "#FFCA28"},
                    {'range': [50, 70], 'color': "#66BB6A"},
                    {'range': [70, 85], 'color': "#26A69A"},
                    {'range': [85, 100], 'color': "#1E88E5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': overall_score
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # Score interpretation
        if overall_score >= 85:
            st.success("Strong market validation with clear demand")
        elif overall_score >= 70:
            st.info("Good validation with some concerns")
        elif overall_score >= 50:
            st.warning("Mixed signals, needs more research")
        elif overall_score >= 30:
            st.error("Weak validation, major concerns")
        else:
            st.error("Little to no validation found")
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 class='sub-header'>Market Validation Summary</h2>", unsafe_allow_html=True)
        st.markdown(f"<p class='insight-text'>{summary}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Create tabs for detailed results
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Pain Points", 
        "Existing Solutions", 
        "Market Opportunities", 
        "Platform Insights",
        "Recommendations"
    ])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Key Pain Points Discovered</h2>", unsafe_allow_html=True)
        for point in pain_points:
            st.markdown(f"- {point}")
        
        # Create word cloud if there are enough pain points
        if len(pain_points) >= 3:
            try:
                # Combine all pain points into a single text
                all_text = " ".join(pain_points)
                
                # Create a DataFrame for word frequency
                words = all_text.split()
                word_freq = pd.DataFrame(words, columns=["word"]).value_counts().reset_index()
                word_freq.columns = ["word", "frequency"]
                
                # Create word cloud using plotly
                fig = px.treemap(
                    word_freq.head(20), 
                    path=["word"], 
                    values="frequency",
                    color="frequency",
                    color_continuous_scale="Blues"
                )
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            except:
                pass  # Skip visualization if it fails
    
    with tab2:
        st.markdown("<h2 class='sub-header'>Existing Solutions Found</h2>", unsafe_allow_html=True)
        for solution in solutions:
            st.markdown(f"- {solution}")
    
    with tab3:
        st.markdown("<h2 class='sub-header'>Market Opportunities</h2>", unsafe_allow_html=True)
        for opportunity in opportunities:
            st.markdown(f"- {opportunity}")
    
    with tab4:
        st.markdown("<h2 class='sub-header'>Platform-Specific Insights</h2>", unsafe_allow_html=True)
        
        # Create columns for each platform
        if platform_insights:
            cols = st.columns(len(platform_insights))
            
            for i, insight in enumerate(platform_insights):
                platform = insight.get("platform", f"Platform {i+1}")
                insights_text = insight.get("insights", "No insights available.")
                
                with cols[i]:
                    st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                    st.markdown(f"<h3>{platform}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p>{insights_text}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
    
    with tab5:
        st.markdown("<h2 class='sub-header'>Recommendations</h2>", unsafe_allow_html=True)
        for recommendation in recommendations:
            st.markdown(f"- {recommendation}")

def run_validation_with_progress(business_idea):
    """Run the validation process with progress indicators."""
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Define the steps and their weights
    steps = [
        ("Generating keywords", 5),
        ("Searching HackerNews", 20),
        ("Searching Reddit", 20),
        ("Scraping Reddit comments", 15),
        ("Analyzing HackerNews posts", 15),
        ("Analyzing Reddit posts", 15),
        ("Generating final report", 10)
    ]
    
    total_weight = sum(weight for _, weight in steps)
    
    # Setup environment to get the data directory
    env = setup_environment(business_idea)
    st.session_state['env'] = env
    run_id = env["run_id"]
    data_dir = env["data_dir"]
    
    # Start the validation process
    validation_thread = None
    
    try:
        # Initialize progress tracking
        progress_state = {
            "current_step": 0,
            "completed_weight": 0,
            "data_dir": data_dir,
            "run_id": run_id,
            "completed": False,
            "analysis": None,
            "error": None
        }
        
        # Start validation in a separate thread
        import threading
        
        def validation_worker():
            try:
                progress_state["analysis"] = validate_business_idea(business_idea)
                progress_state["completed"] = True
            except Exception as e:
                progress_state["error"] = str(e)
                progress_state["completed"] = True
        
        validation_thread = threading.Thread(target=validation_worker)
        validation_thread.start()
        
        # Monitor progress while validation is running
        while not progress_state["completed"]:
            # Check for checkpoint files to determine progress
            current_step = 0
            completed_weight = 0
            
            # Step 1: Keywords
            if os.path.exists(os.path.join(data_dir, "01_keywords.json")):
                current_step = 1
                completed_weight += steps[0][1]
                status_text.text(f"Step 1/7: {steps[0][0]} - Completed")
                
                # Step 2: HackerNews scraping
                hn_complete = os.path.exists(os.path.join(data_dir, "02_hn_posts_complete.json"))
                hn_partial_files = glob.glob(os.path.join(data_dir, "02_hn_posts_partial_*.json"))
                
                if hn_complete:
                    current_step = 2
                    completed_weight += steps[1][1]
                    status_text.text(f"Step 2/7: {steps[1][0]} - Completed")
                elif hn_partial_files:
                    current_step = 2
                    # Calculate partial progress based on number of files
                    partial_progress = len(hn_partial_files) / 10  # Assuming ~10 partial files for full completion
                    partial_progress = min(0.9, partial_progress)  # Cap at 90% for partial completion
                    completed_weight += steps[1][1] * partial_progress
                    status_text.text(f"Step 2/7: {steps[1][0]} - In progress...")
                
                # Step 3: Reddit scraping
                reddit_complete = os.path.exists(os.path.join(data_dir, "03_reddit_posts_complete.json"))
                reddit_partial_files = glob.glob(os.path.join(data_dir, "03_reddit_posts_partial_*.json"))
                
                if reddit_complete:
                    current_step = 3
                    completed_weight += steps[2][1]
                    status_text.text(f"Step 3/7: {steps[2][0]} - Completed")
                elif reddit_partial_files and current_step >= 2:
                    current_step = 3
                    partial_progress = len(reddit_partial_files) / 10
                    partial_progress = min(0.9, partial_progress)
                    completed_weight += steps[2][1] * partial_progress
                    status_text.text(f"Step 3/7: {steps[2][0]} - In progress...")
                
                # Step 4: Reddit comments
                comments_complete = os.path.exists(os.path.join(data_dir, "04_reddit_comments_complete.json"))
                comments_partial_files = glob.glob(os.path.join(data_dir, "04_reddit_comments_partial_*.json"))
                
                if comments_complete:
                    current_step = 4
                    completed_weight += steps[3][1]
                    status_text.text(f"Step 4/7: {steps[3][0]} - Completed")
                elif comments_partial_files and current_step >= 3:
                    current_step = 4
                    partial_progress = len(comments_partial_files) / 5  # Usually fewer comment files
                    partial_progress = min(0.9, partial_progress)
                    completed_weight += steps[3][1] * partial_progress
                    status_text.text(f"Step 4/7: {steps[3][0]} - In progress...")
                
                # Step 5: HN analysis
                hn_analysis_complete = os.path.exists(os.path.join(data_dir, "05_hn_analyses_complete.json"))
                hn_analysis_partial_files = glob.glob(os.path.join(data_dir, "05_hn_analyses_partial_*.json"))
                
                if hn_analysis_complete:
                    current_step = 5
                    completed_weight += steps[4][1]
                    status_text.text(f"Step 5/7: {steps[4][0]} - Completed")
                elif hn_analysis_partial_files and current_step >= 4:
                    current_step = 5
                    partial_progress = len(hn_analysis_partial_files) / 20  # More analysis files
                    partial_progress = min(0.9, partial_progress)
                    completed_weight += steps[4][1] * partial_progress
                    status_text.text(f"Step 5/7: {steps[4][0]} - In progress...")
                
                # Step 6: Reddit analysis
                reddit_analysis_complete = os.path.exists(os.path.join(data_dir, "06_reddit_analyses_complete.json"))
                reddit_analysis_partial_files = glob.glob(os.path.join(data_dir, "06_reddit_analyses_partial_*.json"))
                
                if reddit_analysis_complete:
                    current_step = 6
                    completed_weight += steps[5][1]
                    status_text.text(f"Step 6/7: {steps[5][0]} - Completed")
                elif reddit_analysis_partial_files and current_step >= 5:
                    current_step = 6
                    partial_progress = len(reddit_analysis_partial_files) / 5
                    partial_progress = min(0.9, partial_progress)
                    completed_weight += steps[5][1] * partial_progress
                    status_text.text(f"Step 6/7: {steps[5][0]} - In progress...")
                
                # Step 7: Final analysis
                final_analysis = os.path.exists(os.path.join(data_dir, "07_final_analysis.json"))
                
                if final_analysis:
                    current_step = 7
                    completed_weight += steps[6][1]
                    status_text.text(f"Step 7/7: {steps[6][0]} - Completed")
                elif current_step >= 6:
                    current_step = 7
                    status_text.text(f"Step 7/7: {steps[6][0]} - In progress...")
            else:
                # Still on first step
                status_text.text(f"Step 1/7: {steps[0][0]} - In progress...")
            
            # Update progress bar
            progress_bar.progress(completed_weight / total_weight)
            
            # Sleep briefly to avoid excessive CPU usage
            time.sleep(0.5)
        
        # Check if there was an error
        if progress_state["error"]:
            st.error(f"Error during validation: {progress_state['error']}")
            return None
        
        # Show completion
        progress_bar.progress(1.0)
        status_text.text("Validation complete!")
        
        # Return the analysis
        return progress_state["analysis"]
        
    except Exception as e:
        st.error(f"Error during validation: {e}")
        return None

def main():
    """Main function to run the Streamlit app."""
    # Sidebar
    st.sidebar.markdown("# Business Idea Validator")
    st.sidebar.markdown("Validate your business ideas by analyzing discussions on HackerNews and Reddit.")
    
    # Load previous runs
    previous_runs = load_previous_runs()
    
    # Add option to view previous runs
    if previous_runs:
        st.sidebar.markdown("## Previous Validations")
        selected_run = st.sidebar.selectbox(
            "Select a previous validation to view:",
            options=[f"{run['business_idea']} ({run['timestamp_display']})" for run in previous_runs],
            index=None
        )
        
        view_previous = selected_run is not None
    else:
        view_previous = False
    
    # Main content
    if not view_previous:
        # New validation form
        st.markdown("<h1 class='main-header'>Business Idea Validator</h1>", unsafe_allow_html=True)
        st.markdown(
            "This tool validates business ideas by analyzing discussions on HackerNews and Reddit. "
            "It searches for relevant posts, analyzes them, and generates a validation report."
        )
        
        with st.form("validation_form"):
            business_idea = st.text_area(
                "Enter your business idea:",
                placeholder="e.g., A subscription service for eco-friendly cleaning products",
                height=100
            )
            
            # Advanced options (collapsible)
            with st.expander("Advanced Options"):
                st.markdown("These options will be implemented in a future version.")
                col1, col2 = st.columns(2)
                with col1:
                    st.number_input("Number of keywords to generate:", min_value=1, max_value=10, value=3, disabled=True)
                    st.number_input("Max HackerNews pages per keyword:", min_value=1, max_value=10, value=3, disabled=True)
                with col2:
                    st.number_input("Max Reddit pages per keyword:", min_value=1, max_value=10, value=3, disabled=True)
                    st.number_input("Max Reddit posts to analyze:", min_value=5, max_value=50, value=20, disabled=True)
            
            submitted = st.form_submit_button("Validate Business Idea")
        
        if submitted:
            if not business_idea:
                st.error("Please enter a business idea.")
            else:
                with st.spinner("Validating your business idea. This may take several minutes..."):
                    # Run validation with progress tracking
                    analysis = run_validation_with_progress(business_idea)
                    
                    if analysis:
                        # Convert to dict if it's a Pydantic model
                        if hasattr(analysis, "dict"):
                            analysis_data = analysis.dict()
                        elif isinstance(analysis, str):
                            try:
                                analysis_data = json.loads(analysis)
                            except json.JSONDecodeError:
                                analysis_data = {"error": "Invalid JSON data"}
                        else:
                            analysis_data = analysis
                        
                        # Display results
                        display_validation_results(analysis_data, business_idea)
                        # Add download button for xhs_comments_complete file
                        env = st.session_state['env']
                        data_dir = env["data_dir"]
                        file_location = os.path.join(data_dir, "04_reddit_comments_complete.json")
                        with open(file_location, "rb") as f:
                            st.download_button(
                                label="下载评论数据",
                                data=f,
                                file_name=f"_all_comments.json",
                                mime="application/json",
                                key="all_comments_download"
                            )
    else:
        # Display previous validation results
        selected_index = [f"{run['business_idea']} ({run['timestamp_display']})" for run in previous_runs].index(selected_run)
        run_data = previous_runs[selected_index]
        
        # Load analysis data
        analysis_data = load_analysis_from_file(run_data["final_analysis_path"])
        
        if analysis_data:
            display_validation_results(analysis_data, run_data["business_idea"])
        else:
            st.error("Could not load the selected validation results.")
        # Add download button for xhs_comments_complete file
        if "reddit_comments_complete" in run_data:
            with open(run_data["reddit_comments_complete"], "rb") as f:
                st.download_button(
                    label="下载评论数据",
                    data=f,
                    file_name=f"{run_data['business_idea']}_reddit_comments.json",
                    mime="application/json",
                    key="reddit_comments_download"
                )
    
    # Footer
    st.markdown("<div class='footer'>Business Idea Validator | Created with Streamlit</div>", unsafe_allow_html=True)

# import signal
# import sys

# def signal_handler(sig, frame):
#     print('\nStopping the server...')
#     sys.exit(0)

# signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    main()
