import os
import dotenv
from mcp_bakery_app import tools
from google.adk.agents import LlmAgent

dotenv.load_dotenv()

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'project_not_set')

maps_toolset = tools.get_maps_mcp_toolset()
bigquery_toolset = tools.get_bigquery_mcp_toolset()

root_agent = LlmAgent(
    model='gemini-3-pro-preview',
    name='root_agent',
    instruction=f"""
                Help the user answer questions by strategically combining insights from two sources:
                
                1.  **BigQuery toolset:** Use only the mcp_bakery dataset (four tables: foot_traffic, demographics, bakery_prices, sales_history_weekly). Do not use any other dataset.
                    - foot_traffic: morning/afternoon/evening scores by zip (target discovery)
                    - demographics: census-style population and community profiling
                    - bakery_prices: competitor product pricing
                    - sales_history_weekly: historical sales for forecasting
                    Run all query jobs from project id: {PROJECT_ID}. 

                2.  **Maps Toolset:** Use this for real-world location analysis, finding competition/places and calculating necessary travel routes.
                    Include a hyperlink to an interactive map in your response where appropriate.
            """,
    tools=[maps_toolset, bigquery_toolset]
)

