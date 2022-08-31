# IMPORTING TOOLS
import streamlit as st
from rdflib import Graph, Literal
from rdflib.plugins.sparql import prepareQuery
import pandas as pd
import plotly.express as px
import numpy as np

# SET PAGE SETTINGS
st.set_page_config(page_title='Amusement Accidents', layout="centered")


# METHOD TO LOAD THE RDF
@st.cache(persist=True)
def importRDF(filename, format):
    graph = Graph().parse(filename, format)
    return graph

# IMPORTING THE RDF
with st.spinner('Loading all the stuffs...'):
    graph = importRDF("./RDF/rdf-dataset.ttl", "ttl")

# MOTHOD TO CONVERT THE QUERY RESULT INTO A DATAFRAME
def sparql_results_to_df(results):
    return pd.DataFrame(
        data=([None if x is None else x.toPython() for x in row] for row in results),
        columns=[str(x) for x in results.vars],
    )

# METHOD TO EXECUTE A GENERIC QUERY (and return a pandas dataframe)
def computeQuery(query, executor):
    result = executor.query(query)
    res_df = sparql_results_to_df(result)
    return res_df

# METHOD TO EXECUTE A PARAMETRIC QUERY (select all the accidents description and manufacturer of a user-selected ride)
def rideAccidentDescription(ride_name, executor):
        ride_name = Literal(ride_name)
        query = """
            PREFIX ride_type: <http://example.org/ride_type#>
            PREFIX acc: <http://example.org/accident#>
            PREFIX ride: <http://example.org/ride#>
            SELECT (?manuf AS ?Manufacturer) (?description AS ?Accident_Description)
            WHERE {
                ?instance acc:description ?description ;
                          acc:ref-ride_id ?ride_id .
                ?ride_id ride:name ?name ;
                         ride:manufacturer ?manuf .
                FILTER (?name = ?ride_name)
            }
        """
        prep_query = prepareQuery(query)
        r = executor.query(prep_query, initBindings={'ride_name': ride_name})
        return sparql_results_to_df(r), query

# PROCESSING & DISPLAY
def display():
    with st.container():
        st.write("#### What are the months with the highest number of accidents?")
        res = computeQuery(query_5, graph)
        fig = px.bar(res, x="mon", y="count", color="count", labels={"mon":"Month", "count":"Num. of Accidents"}, text_auto="True")
        fig.update_xaxes(type="category")
        fig.update_yaxes(showticklabels=False)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Show query"):
            st.code(query_5, language="sparql")
        st.markdown("---")

    with st.container():
        st.write("#### Which cities and states have recorded the most accidents?")
        res = computeQuery(query_8, graph)
        fig = px.treemap(res, path=[px.Constant("U.S"), "state", "city"], values="count", hover_data=["state", "city","count"],
                color="count",
                color_continuous_scale='tealrose',
                color_continuous_midpoint=np.average(res['count'], weights=res['count']))
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Show query"):
            st.code(query_8, language="sparql")
        st.markdown("---")

    with st.container():
        st.write("#### What incidents have occurred on your favorite ride?")
        ride_names = computeQuery(query_0, graph)
        option = st.selectbox("Select a Ride", options=ride_names)
        res, query = rideAccidentDescription(option, graph)
        res_count = res.count()[0]
        limit = st.slider("Num. of Accidents to Visualize", 1, int(res_count), 5, 1)
        st.table(res[:limit])
        with st.expander("Show query"):
            st.code(query, language="sparql")
        st.markdown("---")

    with st.container():
        st.write("#### What Are the Most Common Categories of Accidents?")
        res = computeQuery(query_4, graph)
        fig = px.treemap(res, path=[px.Constant("Accident Category"), "category_name"], values="count", hover_data=["category_name","count"])
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Show query"):
            st.code(query_4, language="sparql")
        st.markdown("---")

    with st.container():
        st.write("#### What are the Most Dangerous Ride Categories?")
        res = computeQuery(query_6, graph)
        fig = px.pie(res, names="amus_cat_name", values="count", hole=.4)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Show query"):
            st.code(query_6, language="sparql")
        st.markdown("---")

    with st.container():
        st.write("#### What are the Most Dangerous Ride Types?")
        res = computeQuery(query_3, graph)
        fig = px.bar(res, x="type_name", y="count", labels={"type_name":"Ride Type", "count":"Num. of Accidents"}, text_auto=True)
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Show query"):
            st.code(query_3, language="sparql")
        st.markdown("---")

    with st.container():
        st.write("#### How many people are generally involved in an accident?")
        res = computeQuery(query_1, graph)
        fig = px.bar(res, x="num_inj", y="count", labels={"num_inj":"Injured People", "count":"Num. of Accidents"}, text_auto=True)
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Show query"):
            st.code(query_1, language="sparql")
        st.markdown("---")

    return None

# ANALYTICAL QUERIES DEFINITION
# get the names of all the rides
query_0 = """
    PREFIX ride:<http://example.org/ride#>        

    SELECT DISTINCT ?name
    WHERE {
        ?ride ride:name ?name .
    }
"""
# num of accidents per injured people
query_1 = """
    PREFIX r:<http://example.org/ride#>
    PREFIX a:<http://example.org/accident#>

    SELECT ?num_inj (COUNT(?num_inj) AS ?count) 
    WHERE {
        ?acc a:num_injured ?num_inj .
    }
    GROUP BY ?num_inj
    ORDER BY (?num_inj)
"""

# manufacturers of the rides subjected to most accidents
query_2 = """
    PREFIX acc: <http://example.org/accident#>
    PREFIX ride: <http://example.org/ride#>

    SELECT ?ride_manuf (COUNT(?ride_manuf) AS ?count)
    WHERE {
        ?instance acc:ref-ride_id ?ride_id .
        ?ride_id ride:manufacturer ?ride_manuf
    }
    GROUP BY ?ride_manuf
    ORDER BY DESC(?count)
"""

# Top n types of rides most subjected to accidents
query_3 = """
    PREFIX ride_type: <http://example.org/ride_type#>
    PREFIX acc: <http://example.org/accident#>
    PREFIX ride: <http://example.org/ride#>

    SELECT ?type_name (COUNT(?type_name) AS ?count)
    WHERE {
        ?instance acc:ref-ride_id ?ride_id .
        ?ride_id ride:ref-ride_type_id ?type_id .
        ?type_id ride_type:type ?type_name .
    }
    GROUP BY ?type_name
    ORDER BY DESC(?count)
    LIMIT 7
"""

# Top 6 categories of rides most subjected to accidents
query_6 = """
    PREFIX amusement_cat: <http://example.org/amusement_category#>
    PREFIX ride_type: <http://example.org/ride_type#>
    PREFIX acc: <http://example.org/accident#>
    PREFIX ride: <http://example.org/ride#>

    SELECT ?amus_cat_name (COUNT(?amus_cat_name) AS ?count)
    WHERE {
        ?instance acc:ref-ride_id ?ride_id .
        ?ride_id ride:ref-ride_type_id ?type_id .
        ?type_id ride_type:ref-amusement_category_id ?amus_cat_id .
        ?amus_cat_id amusement_cat:amusement_category ?amus_cat_name .
    }
    GROUP BY ?amus_cat_name
    ORDER BY DESC(?count)
    LIMIT 6
    
"""

# most common categories of accidents
query_4 = """
    PREFIX acc_cat: <http://example.org/accident_category#>
    PREFIX acc: <http://example.org/accident#>

    SELECT ?category_name (COUNT(?category_name) AS ?count)
    WHERE {
        ?instance acc:ref-accident_category_id ?category_id .
        ?category_id acc_cat:accident_category ?category_name .
    }
    GROUP BY ?category_name
    ORDER BY DESC(?count)
"""

# months with the ngher num of accidents
query_5 = """
    PREFIX acc: <http://example.org/accident#>

    SELECT ?mon (COUNT(?mon) AS ?count)
    WHERE {
        ?instance acc:date ?date .
    }
    GROUP BY (month(?date) AS ?mon)
    ORDER BY (?mon)
"""

# cities with the higher num of accidents
query_8 = """
    PREFIX location: <http://example.org/location#>
    PREFIX acc: <http://example.org/accident#>

    SELECT ?city (COUNT(?city) AS ?count) ?state
    WHERE {
        ?instance acc:ref-location_id ?location_id .
        ?location_id location:city ?city ;
                     location:state ?state
    }
    GROUP BY ?city
    ORDER BY DESC(?count)
    
"""


# TITLE
st.header("Theme Park Ride Accidents")
st.markdown("""There are **thousands of amusement parks** around the world that welcome **millions of visitors** each year. 
    Children, families, and teenagers are ready to spend days of adrenaline and fun. 
    Unfortunately, **accidents sometimes occur**. This raises some questions: **Are amusement parks safe? Which rides are the most accident-prone? What accidents happen most often? At what time of year are accidents most common?** 
    Let's try to find out in this **RDF data exploration** using **SPARQL** and **Plotly**.""")
st.markdown("---")

display()

# WRITE & RUN YOUR OWN QUERY
st.write("#### Write & Run your Custom Query")
pers_query = st.text_area('', """
    PREFIX ride:<http://example.org/ride#>
    SELECT ?name
    WHERE {
        ?ride ride:manufacturer "Vekoma" ;
              ride:name ?name
    }
""", height=200)
with st.container():
    res = computeQuery(pers_query, graph)
    st.table(res)
    st.markdown("---")

# SIDEBAR
with st.sidebar:
    st.write("""
    This App proposes some visualization about theme park ride accidents. 
    The original dataset comes from "Saferparks", an organization that reports and collects data about theme park ride accidents in the US. 
    The original dataset covers years from 2010 to 2017 and comes in CSV or Excel format. I used python to split the dataset and convert it into the 
    Third Normal Form (3NF) of Database.
    I uploaded the data into a PostgreSQL database and I used the Ontop tool to get the final RDF dataset. 
    Queries are expressed in SPARQL, and charts are generated with Plotly Express.
        """)
    st.markdown("---")
    st.markdown("## Dataset Resources:")
    st.markdown("""
        Saferparks Original Dataset: https://ridesdatabase.org/saferparks/data/

        Saferparks Dataset Description: https://ridesdatabase.org/wp-content/uploads/2020/02/Saferparks-data-description.pdf
        """)
