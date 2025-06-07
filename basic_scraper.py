
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_url(url):
    """
    Scrape the HTML content from a given URL
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        tuple: (raw_html, parsed_html, status_code, headers)
    """
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers)
        
        # Get the raw HTML
        raw_html = response.text
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        return raw_html, soup, response.status_code, response.headers
    
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None, None, None

# Set up the Streamlit UI
st.title("Basic Web Scraper")

# URL input
url = st.text_input("Enter a URL to scrape:", "https://example.com")

# Scraping options
with st.expander("Scraping Options"):
    show_raw_html = st.checkbox("Show Raw HTML", value=True)
    show_parsed_elements = st.checkbox("Show Parsed Elements", value=True)
    show_headers = st.checkbox("Show Response Headers", value=False)

# Scrape button
if st.button("Scrape URL"):
    with st.spinner("Scraping..."):
        raw_html, soup, status_code, headers = scrape_url(url)
        
        if raw_html:
            st.success(f"Successfully scraped URL with status code: {status_code}")
            
            # Display tabs for different views of the scraped content
            tab1, tab2, tab3, tab4 = st.tabs(["Raw HTML", "Parsed Elements", "Headers", "Data Preview"])
            
            with tab1:
                if show_raw_html:
                    st.subheader("Raw HTML")
                    st.code(raw_html, language="html")
                else:
                    st.info("Enable 'Show Raw HTML' to view the raw HTML content.")
            
            with tab2:
                if show_parsed_elements and soup:
                    st.subheader("Parsed Elements")
                    
                    # Show all links
                    st.write("### Links")
                    links = soup.find_all('a')
                    if links:
                        link_data = []
                        for link in links[:20]:  # Limit to first 20 links
                            link_data.append({
                                "Text": link.text.strip(),
                                "URL": link.get('href', '')
                            })
                        st.dataframe(pd.DataFrame(link_data))
                        
                        if len(links) > 20:
                            st.info(f"Showing 20 of {len(links)} links found.")
                    else:
                        st.write("No links found.")
                    
                    # Show all headers
                    st.write("### Headers (h1, h2, h3)")
                    headers_elements = soup.find_all(['h1', 'h2', 'h3'])
                    if headers_elements:
                        header_data = []
                        for header in headers_elements:
                            header_data.append({
                                "Type": header.name,
                                "Text": header.text.strip()
                            })
                        st.dataframe(pd.DataFrame(header_data))
                    else:
                        st.write("No headers found.")
                else:
                    st.info("Enable 'Show Parsed Elements' to view the parsed elements.")
            
            with tab3:
                if show_headers:
                    st.subheader("Response Headers")
                    st.json(dict(headers))
                else:
                    st.info("Enable 'Show Response Headers' to view the headers.")
            
            with tab4:
                st.subheader("Data Preview")
                st.write("This tab is where you would display extracted data in a structured format.")
                st.write("For example, if you were scraping a product page, you might extract:")
                
                # Example of what extracted data might look like
                example_data = {
                    "Title": soup.title.text if soup.title else "N/A",
                    "URL": url,
                    "Number of links": len(soup.find_all('a')) if soup else 0,
                    "Number of images": len(soup.find_all('img')) if soup else 0,
                }
                
                st.json(example_data)
        else:
            st.error("Failed to scrape the URL. Please check the URL and try again.")

# Add some helpful information
st.markdown("---")
st.info("""
This is a basic web scraper for testing purposes. Be mindful of the following:
1. Some websites do not allow scraping and may block your requests
2. Always check a website's robots.txt file and terms of service before scraping
3. This is a simple demo and lacks features like request throttling, proxies, or handling of JavaScript-rendered content
""")