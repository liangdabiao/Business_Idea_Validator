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
from openai import OpenAI
import instructor
from business_validator import validate_business_idea_cn
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
            xhs_comments_complete = os.path.join(subdir, "04_xhs_comments_complete.json")
            xhs_analyses_complete = os.path.join(subdir, "06_xhs_analyses_complete.json")
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
                    "final_analysis_path": final_analysis_path,
                    "xhs_comments_complete": xhs_comments_complete,
                    "xhs_analyses_complete": xhs_analyses_complete
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

def display_validation_results(analysis_data, business_idea ,xhs_comments_complete_file):
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
    col1, col2, col3 = st.columns([1, 2, 2])
    
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

    with col3:
        st.header("AI对话分析")
        st.write("请继续进行更多的数据分析，直接问我就可以！")
        
        # if 'recommendations' in st.session_state:
        #     st.write("推荐内容:")
        #     for rec in st.session_state['recommendations']:
        #         st.write(f"- {rec}")
        

        # 初始化聊天历史
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        def get_chatgpt_response(prompt):
            # 建议从环境变量获取API密钥
            OPENAI_API_KEY = "fk21f6DATB3qMgwe"  
            OPENAI_BASE_URL = "https://openai.api2d.net/v1"
        
            try:
                openai_client = OpenAI(api_key=OPENAI_API_KEY,base_url=OPENAI_BASE_URL)
                instructor.patch(openai_client)
                response = openai_client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": "你是一个有帮助的AI助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"API调用出错: {str(e)}"

        # 显示聊天历史
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_history:
                st.markdown(f"​**​{msg['role']}​**: {msg['content']}")

        # 使用表单获取用户输入
        with st.form(key='chat_form'):
            user_input = st.text_input("请输入您的问题:", key="user_input")
            submitted = st.form_submit_button("提交") 
            if submitted and user_input: 
                with st.spinner('AI正在思考...'): 
                     # 消息处理逻辑
                     
                    all_comments = ''
                    file_location = xhs_comments_complete_file
                    with open(file_location, "rb") as f:
                        all_comments = f.read()
                           

                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    prompt_txt = f"""
                    你是一个有帮助的AI助手。
                    你将根据以下评论内容回答用户的问题：
                    评论内容:#### {all_comments} #### ，
                    用户问题： {user_input} """
                    #print(prompt_txt)
                    response = get_chatgpt_response(prompt_txt)
                    st.session_state.chat_history.append({"role": "ai", "content": response})
                    st.rerun()  # 强制重新渲染界面




 

def run_validation_with_progress(business_idea):
    """Run the validation process with progress indicators."""
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    some_txt = st.empty()
    some_txt_xhs_posts_complete = st.empty()
    some_txt_xhs_analyses_complete = st.empty()
    
    # Define the steps and their weights
    steps = [
        ("Generating keywords", 5),
        ("Searching HackerNews", 20),
        ("Searching XHS", 20),
        ("Scraping XHS comments", 15),
        ("Analyzing HackerNews posts", 15),
        ("Analyzing XHS posts", 15),
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
                progress_state["analysis"] = validate_business_idea_cn(business_idea)
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
                # some_txt.text("正在生成关键词...")
                # some_txt 显示  "01_keywords.json" 文件内容
                with open(os.path.join(data_dir, "01_keywords.json"), 'r', encoding='utf-8') as f:
                    keywords_data = json.load(f)
                    keywords = keywords_data.get("keywords", [])
                    some_txt.text(f"关键词: {keywords}")
                
                # Step 2: HackerNews scraping
                hn_complete = os.path.exists(os.path.join(data_dir, "02_hn_posts_complete.json"))
                hn_partial_files = glob.glob(os.path.join(data_dir, "02_hn_posts_partial_*.json"))

                
                # Step 3: xhs scraping
                xhs_complete = os.path.exists(os.path.join(data_dir, "03_xhs_posts_complete.json"))
                xhs_partial_files = glob.glob(os.path.join(data_dir, "03_xhs_posts_partial_*.json"))
                
                if xhs_complete:
                    current_step = 3
                    completed_weight += steps[2][1]
                    status_text.text(f"Step 3/7: {steps[2][0]} - Completed")
                    # show some_txt_xhs_posts_complete
                    with open(os.path.join(data_dir, "03_xhs_posts_complete.json"), 'r', encoding='utf-8') as f:
                        xhs_posts_data = json.load(f)
                        xhs_posts = xhs_posts_data.get("xhs_posts", []) 
                        some_txt_xhs_posts_complete.code(json.dumps(xhs_posts, indent=2, ensure_ascii=False), language='json')
                elif xhs_partial_files and current_step >= 2:
                    current_step = 3
                    partial_progress = len(xhs_partial_files) / 10
                    partial_progress = min(0.9, partial_progress)
                    completed_weight += steps[2][1] * partial_progress
                    status_text.text(f"Step 3/7: {steps[2][0]} - In progress...")
                    last_xhs_partial_files = xhs_partial_files[-1] if xhs_partial_files else None
                    with open(os.path.join(data_dir, last_xhs_partial_files), 'r', encoding='utf-8') as f:
                        xhs_posts_data = json.load(f)
                        xhs_posts = xhs_posts_data.get("xhs_posts", [])
                        some_txt_xhs_posts_complete.code(json.dumps(xhs_posts, indent=2, ensure_ascii=False), language='json')
                
                # Step 4: xhs comments
                comments_complete = os.path.exists(os.path.join(data_dir, "04_xhs_comments_complete.json"))
                comments_partial_files = glob.glob(os.path.join(data_dir, "04_xhs_comments_partial_*.json"))
                
                if comments_complete:
                    current_step = 4
                    completed_weight += steps[3][1]
                    status_text.text(f"Step 4/7: {steps[3][0]} - Completed")
                    # show  some_txt_xhs_comments_complete
                    with open(os.path.join(data_dir, "04_xhs_comments_complete.json"), 'r', encoding='utf-8') as f:
                        xhs_comments_data = json.load(f)
                        xhs_posts_with_comments = xhs_comments_data.get("xhs_posts_with_comments", []) 
                        some_txt_xhs_posts_complete.code(json.dumps(xhs_posts_with_comments, indent=2, ensure_ascii=False), language='json')
                elif comments_partial_files and current_step >= 3:
                    current_step = 4
                    partial_progress = len(comments_partial_files) / 5  # Usually fewer comment files
                    partial_progress = min(0.9, partial_progress)
                    completed_weight += steps[3][1] * partial_progress
                    status_text.text(f"Step 4/7: {steps[3][0]} - In progress...")
                    # show  some_txt_xhs_comments_complete
                    last_comments_partial_files = comments_partial_files[-1] if comments_partial_files else None
                    with open(last_comments_partial_files, 'r', encoding='utf-8') as f:
                        xhs_comments_data = json.load(f)
                        xhs_posts_with_comments = xhs_comments_data.get("xhs_posts_with_comments", []) 
                        #some_txt_xhs_posts_complete.code(json.dumps(xhs_posts_with_comments, indent=2, ensure_ascii=False), language='json')
                
                
                # Step 6: xhs analysis
                xhs_analysis_complete = os.path.exists(os.path.join(data_dir, "06_xhs_analyses_complete.json"))
                xhs_analysis_partial_files = glob.glob(os.path.join(data_dir, "06_xhs_analyses_partial_*.json"))
                
                if xhs_analysis_complete:
                    current_step = 6
                    completed_weight += steps[5][1]
                    status_text.text(f"Step 6/7: {steps[5][0]} - Completed")
                    # show some_txt_xhs_analyses_complete
                    with open(os.path.join(data_dir, "06_xhs_analyses_complete.json"), 'r', encoding='utf-8') as f:
                        xhs_analyses_complete_data = json.load(f) 
                        some_txt_xhs_analyses_complete.code(json.dumps(xhs_analyses_complete_data, indent=2, ensure_ascii=False), language='json')
                elif xhs_analysis_partial_files and current_step >= 5:
                    current_step = 6
                    partial_progress = len(xhs_analysis_partial_files) / 5
                    partial_progress = min(0.9, partial_progress)
                    completed_weight += steps[5][1] * partial_progress
                    status_text.text(f"Step 6/7: {steps[5][0]} - In progress...")
                    last_analysis_partial_files = xhs_analysis_partial_files[-1] if xhs_analysis_partial_files else None
                    with open(last_analysis_partial_files, 'r', encoding='utf-8') as f:
                        xhs_analysis_partial_data = json.load(f) 
                        #some_txt_xhs_analyses_complete.code(json.dumps(xhs_analysis_partial_data, indent=2, ensure_ascii=False), language='json')
                
                
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

        # 页面滚动到最下
        st.markdown("""
        <script>
            setTimeout(function() {
                window.scrollTo(0, document.body.scrollHeight);
            }, 100);
        </script>
        """, unsafe_allow_html=True)

        
        # Return the analysis
        return progress_state["analysis"]
        
    except Exception as e:
        st.error(f"Error during validation: {e}")
        return None

def main():
    

    """Main function to run the Streamlit app."""
    # Sidebar
    st.sidebar.markdown("# Business Idea Validator")
    st.sidebar.markdown("Validate your business ideas by analyzing discussions on XHS（小红书）.")
    
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
            "This tool validates business ideas by analyzing discussions on XHS. "
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
                    st.number_input("Max xhs pages per keyword:", min_value=1, max_value=10, value=3, disabled=True)
                    st.number_input("Max xhs posts to analyze:", min_value=5, max_value=50, value=20, disabled=True)
            
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
                        # Add download button for xhs_comments_complete file
                        env = st.session_state['env']
                        data_dir = env["data_dir"]
                        file_location = os.path.join(data_dir, "04_xhs_comments_complete.json")

                        display_validation_results(analysis_data, business_idea,file_location)

                        
                        with open(file_location, "rb") as f:
                            st.download_button(
                                label="下载小红书评论数据",
                                data=f,
                                file_name=f"_xhs_comments.json",
                                mime="application/json",
                                key="xhs_comments_download"
                            )
                        
    else:
        # Display previous validation results
        selected_index = [f"{run['business_idea']} ({run['timestamp_display']})" for run in previous_runs].index(selected_run)
        run_data = previous_runs[selected_index]
        
        # Load analysis data
        analysis_data = load_analysis_from_file(run_data["final_analysis_path"])
        
        if analysis_data:
            display_validation_results(analysis_data, run_data["business_idea"],run_data["xhs_comments_complete"])
        else:
            st.error("Could not load the selected validation results.")

        # Add download button for xhs_comments_complete file
        if "xhs_comments_complete" in run_data:
            with open(run_data["xhs_comments_complete"], "rb") as f:
                st.download_button(
                    label="下载小红书评论数据",
                    data=f,
                    file_name=f"{run_data['business_idea']}_xhs_comments.json",
                    mime="application/json",
                    key="xhs_comments_download"
                )
    
    # Footer
    st.markdown("<div class='footer'>Business Idea Validator | Created with Streamlit</div>", unsafe_allow_html=True)

# import signal
# import sys

# def signal_handler(sig, frame):
#     print('\nStopping the server...')
#     sys.exit(0)

# signal.signal(signal.SIGIN, signal_handler)


if __name__ == "__main__":

    main()
    
     
    
    
    
