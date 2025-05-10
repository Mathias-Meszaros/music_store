import streamlit as st
import pandas as pd
import pyodbc
import altair as alt

conn = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=DellPrecision\\SQLEXPRESS;"
    "Database=Store;"
    "Trusted_Connection=yes;"
)

st.set_page_config(page_title="Zeneáruház riport", layout="wide")
st.title("Music Store Analysis")

queries = [
    ("Customers by country", """
        select Country, count(*) as Customer_Count
        from Customer
        group by Country
        order by Customer_Count desc;
    """),

    ("Customers total purchases", """
        select c.FirstName, c.Lastname, sum(i.Total) as Total_Spent
        from Customer c
        join Invoice i on c.CustomerId = i.CustomerId
        group by c.FirstName, c.LastName
        order by Total_Spent desc;
    """),

    ("Artist's albums", """
        select Artist.Name, count(Album.Title) as Albums_Count
        from Artist
        join Album on Album.Artistid = Artist.ArtistId
        group by Artist.Name
        order by Albums_Count desc;
    """),

    ("Annual sales volume", """
        select year(InvoiceDate) as Year, count(*) as Invoice_Count
        from Invoice
        group by year(InvoiceDate)
        order by count(*) desc;
    """),

    ("Sales by genre", """
        select Genre.Name as Genre, count(InvoiceLine.InvoiceLineId) as Sold_Track
        from Genre
        join Track on Genre.GenreId = Track.GenreId
        join InvoiceLine on InvoiceLine.TrackId = Track.TrackId
        group by Genre.Name
        order by count(InvoiceLine.InvoiceLineId) desc;
    """),

    ("Customers who have made more than 5 purchases", """
        select c.FirstName, c.LastName, count(i.InvoiceId) as NumberOfPurchases
        from Customer c
        join Invoice i on c.CustomerId = i.CustomerId
        group by c.FirstName, c.LastName
        having count(i.InvoiceId) > 5 
        order by NumberOfPurchases desc;
    """),

    ("Countries where number of customers 5 or more than", """
        select Country, count(*) as Customers 
        from Customer
        group by Country
        having count(*) >= 5
        order by count(*) desc;
    """),

    ("Countries where total sales are more than 100", """
        with Sales_By_Country as (
            select c.Country, sum(i.Total) as Total_Sales 
            from Customer c
            join Invoice i on c.CustomerId = i.CustomerId
            group by c.Country
        )
        select *
        from Sales_By_Country
        where Total_Sales > 100
        order by Total_Sales desc;
    """),

    ("The top 3 countries with sales exceeding 100", """
        with Sales_By_Country as (
            select c.Country, sum(i.Total) as Total_Sales
            from Customer c
            join Invoice i on c.CustomerId = i.CustomerId
            group by c.Country
        ),
        High_Sales_Countries as (
            select Country, Total_Sales as Total_Sales
            from Sales_By_Country
            where Total_Sales > 100
        ),
        Top_countries as (
            select top 3 Country, Total_Sales 
            from High_Sales_Countries
            order by Total_Sales desc
        )
        select * 
        from top_countries;
    """),

    ("VIP buyers and sales countries", """
        with Sales_By_Country as (
            select c.Country, count(distinct c.CustomerId) as Customers, sum(i.Total) as Sales
            from Customer c
            join Invoice i on c.CustomerId = i.CustomerId
            group by c.Country
        ),
        Classified_Countries as (
            select Country, Customers, Sales,
            case
                when Sales > 500 then 'VIP Countries'
                when Sales between 100 and 500 then 'Standard Countries'
                else 'Low Countries'
            end as Categories
            from Sales_By_Country
        ),
        Top_Countries as (
            select Country, Customers, Sales, Categories
            from Classified_Countries
            where Customers >= 3
        )
        select *
        from Top_Countries
        order by Sales desc;
    """),

    ("Countries where there were at least 5 sales", """
        with Country_Customer_Sales as (
            select c.Country, count(distinct c.CustomerId) as Customers, sum(i.Total) as Sales
            from Customer c	
            join Invoice i on i.CustomerId = c.CustomerId
            group by Country
        )
        select Country, Customers, Sales
        from Country_Customer_Sales
        where Customers >= 5
        order by Sales desc;
    """),

    ("Countries where there were at least 3 sales", """
        with Total_Sales as (
            select c.Country, count(distinct c.CustomerId) as Customers, sum(i.Total) as Sales	
            from Customer c
            join Invoice i on c.CustomerId = i.CustomerId
            group by c.Country
            having count(distinct c.CustomerId) >= 3
        ),
        Sales_Category as (
            select Country, Sales, Customers,
            case 
                when Sales >= 500 then 'High Sales'
                when Sales between 100 and 500 then 'Medium Sales'
                else 'Low Sales'
            end as Category
            from Total_Sales
        )
        select *
        from Sales_Category
        order by Sales desc;
    """),

    ("Categorize customers based on purchase", """
        with Customers_Spents as (
            select C.FirstName as First_Name, C.LastName as Last_Name, count(I.InvoiceId) as Total_Order, sum(I.Total) as Total_Spent	
            from Customer C
            join Invoice I on C.CustomerId = I.CustomerId
            group by C.FirstName, C.LastName
            having count(I.InvoiceId) >= 3
        ),
        Category_Invocie as (
            select First_name, Last_name, Total_Order, Total_Spent,
            case 
                when Total_Spent >= 45 then 'Platinum'
                when Total_Spent between 38 and 45 then 'Gold'
                else 'Silver'
            end as Category
            from Customers_Spents
        )
        select * 
        from Category_Invocie
        order by Total_Spent desc;
    """),

    ("Employee performance", """
        with Employee_Performance as (
            select E.FirstName as First_Name, E.LastName as Last_Name, count(distinct C.CustomerId) as Customers_Count, sum(I.Total) as Total_Spent
            from Employee E
            join Customer C on E.EmployeeId = C.SupportRepId
            join Invoice I on C.CustomerId = I.CustomerId
            group by E.EmployeeId, E.FirstName, E.LastName
            having count(distinct C.CustomerId) >= 2
        )
        select *,
        case 
            when Total_Spent > 300 then 'Top Performer'
            when Total_Spent between 100 and 300 then 'Solid Performer'
            else 'Needs Improvement'
        end as Performance
        from Employee_Performance
        order by Total_Spent desc;
    """),

    ("Album revenue", """
        select A.Title as Album, Ar.Name as Artist, count(T.TrackId) as Track_Count, sum(IL.UnitPrice) as Total_Revenue
        from Album A
        join Artist Ar on Ar.ArtistId = A.ArtistId
        join Track T on T.AlbumId = A.AlbumId
        join InvoiceLine IL on IL.TrackId = T.TrackId
        group by A.AlbumId, A.Title, Ar.Name
        having count(T.TrackId) >= 5
        order by Total_Revenue desc;
    """),

    ("Annual purchases", """
        with Annual_Purchases as (
            select year(InvoiceDate) as Year, count(InvoiceId) as Total_Transactions, sum(Total) as Total_Revenue
            from Invoice
            group by year(InvoiceDate)
        )
        select Year, Total_Transactions, Total_Revenue,
        case
            when Total_Revenue > 600 then 'Outstanding Year'
            when Total_revenue between 300 and 600 then 'Average Year'
            else 'Weak Year'
        end as Revenue_Category
        from Annual_Purchases
        order by Year asc;
    """)
]

for title, query in queries:
    st.subheader(title)
    try:
        df = pd.read_sql_query(query, conn)
        st.dataframe(df, use_container_width=True)
        
        if "Country" in df.columns and "Customer_Count" in df.columns:
            st.bar_chart(df.set_index("Country"))

        elif "LastName" in df.columns and "Total_Spent" in df.columns:
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('LastName:N', sort='-y'),
                y='Total_Spent:Q',
                tooltip=['FirstName', 'LastName', 'Total_Spent']
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

        elif "Genre" in df.columns and "Sold_Track" in df.columns:
            st.bar_chart(df.set_index("Genre"))

        elif "Year" in df.columns and "Invoice_Count" in df.columns:
            st.line_chart(df.set_index("Year"))

        elif "Country" in df.columns and "Total_Sales" in df.columns:
            st.bar_chart(df.set_index("Country"))

        elif "Artist" in df.columns and "Total_Revenue" in df.columns:
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('Artist:N', sort='-y'),
                y='Total_Revenue:Q',
                tooltip=['Artist', 'Album', 'Total_Revenue']
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

        elif "Year" in df.columns and "Total_Revenue" in df.columns:
            st.line_chart(df.set_index("Year")["Total_Revenue"])

    except Exception as e:
        st.error(f"Error in '{title}'\n{e}")

