import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

##################################################
##### Read in dataset initially
##################################################

@st.cache_data
def fetch_location_data():
    logger.info("Fetching location data")
    df = pd.read_excel('School Location 2023.xlsx', sheet_name='SchoolLocations 2023')
    #df = pd.read_csv('School Location 2023.csv')
    logger.info(f"Loaded {len(df)} schools")
    return df

##################################################
##### Main Application
##################################################

st.set_page_config(layout="wide")


def main():
    # Set up page title and description
    st.subheader("Count of Australian Schools 2023, by Local Government Area")
    #st.subheader("This is a subtitle or additional information.")
    #st.sidebar.title('Sidebar is here')
    #st.sidebar.image('F3C_Canva.png')

    # Create two columns - one for map, one for info
    #col1, col2 = st.columns([10, 10])
    col1, col2 = st.columns([3,1])
          
    # Get the data
    df_loc = fetch_location_data()
    
    df_lga = df_loc.groupby(['State','Local Government Area Name']).agg(Latitude=('Latitude',np.mean)
                                                                        ,Longitude=('Longitude',np.mean)
                                                                        ,School_Count=('School Name','count')
                                                                        ).reset_index()
    
    def get_radius(metric,max_x):
        if metric == 0:
            return 5
        elif metric <= max_x/5*1:
            return 7
        elif metric <= max_x/5*2:
            return 10
        elif metric <= max_x/5*3:
            return 13
        elif metric <= max_x/5*4:
            return 16
        else:
            return 20

    def get_colour(metric,max_x):
        if metric <= 5:
            return 'darkgreen'
        elif metric <= 15:
            return 'lightgreen'
        elif metric <= 30:
            return 'yellow'
        elif metric <= 50:
            return 'orange'
        elif metric <= max_x:
            return 'red'        
        else:
            return 'gray'  
                 
    # Create base map
    m = folium.Map(location=[-25.2744, 133.7751], zoom_start=4)

    # Add markers with unique IDs
    for idx, row in df_lga.iterrows():
        color=get_colour(row['School_Count'], df_lga['School_Count'].max())
        #folium.CircleMarker(
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=get_radius(row['School_Count'], df_lga['School_Count'].max()),
            popup=f"<b>Local Government Area:</b><br>{row['Local Government Area Name']}<br>"
                  f"<b>State:</b><br>{row['State']}<br>"
                  f"<b>School Count:</b><br>{row['School_Count']}",
            tooltip=f"<b>Local Government Area:</b><br>{row['Local Government Area Name']}<br>"
                    f"<b>State:</b><br>{row['State']}<br>"
                    f"<b>School Count:</b><br>{row['School_Count']}",
            #color=get_colour(row['School_Count'], df_lga['School_Count'].max()),
            #icon=folium.Icon(color=color),
            #color='darkgreen',
            color=color,
            #radius=10,
            fill=True,
            #fill_color='blue',
            name=f"marker_{idx}"  # Add unique identifier
        ).add_to(m)
    
    with col1:
        # Display map and get results with all possible return objects
        map_result = st_folium(
            m,
            width=1500,
            height=700,
            returned_objects=["last_clicked", "last_object_clicked", "all_drawings"]
        )
    # Show click information in the second column
    with col2:
        st.subheader("Click an area to display School Names")
        # Debug logging for all map interactions
        if map_result:
            logger.info("Map interaction detected")
            logger.info(f"Map result keys: {map_result.keys()}")
            logger.info(f"Full map result: {map_result}")
            
            # Check for marker/object click
            if 'last_object_clicked' in map_result and map_result['last_object_clicked']:
                logger.info("Marker clicked!")
                logger.info(f"Clicked object: {map_result['last_object_clicked']}")
                clicked_lat = map_result['last_object_clicked']['lat']
                clicked_lng = map_result['last_object_clicked']['lng']                
                st.write(f"Map area clicked.") 
                st.write(f"Lat: {map_result['last_object_clicked']['lat']}")
                st.write(f"Long: {map_result['last_object_clicked']['lng']}")              

                try:
                    # Try exact match first
                    lga_filter = df_lga[(df_lga['Latitude']==clicked_lat) & 
                                       (df_lga['Longitude']==clicked_lng)]
                    
                    if len(lga_filter) > 0:
                        st.write("📍 Exact location match")
                        st.write(f"LGA: {lga_filter['Local Government Area Name'].to_list()[0]}")
                        
                    else:
                        # If no exact match, find closest LGA using simple absolute difference
                        st.write("⚠️ Closest match found")
                        
                        # Calculate absolute differences and sum them
                        df_lga['diff'] = (abs(df_lga['Latitude'] - clicked_lat) + 
                                        abs(df_lga['Longitude'] - clicked_lng))
                        
                        # Get closest LGA
                        closest_lga = df_lga.loc[df_lga['diff'].idxmin()]
                        st.write(f"Closest LGA: {closest_lga['Local Government Area Name']}")
                        
                        # Filter for closest LGA
                        lga_filter = df_lga[df_lga['Local Government Area Name'] == 
                                          closest_lga['Local Government Area Name']]
                    
                    # Get and display school list
                    filter_list = df_loc.merge(lga_filter[['State','Local Government Area Name']],
                                             on=['State','Local Government Area Name'])
                    filter_list = filter_list[['School Name']]
                    st.dataframe(filter_list,hide_index=True)#,use_contaner_width=True)
                    
                except Exception as e:
                    logger.info(f"Error in processing: {str(e)}")
                    st.error("An error occurred while processing your request.")

if __name__ == "__main__":
    main()
    
