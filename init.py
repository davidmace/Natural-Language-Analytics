"""
This is a database preprocessing script so it fetches a bunch of data that we need for later
processing of queries in processQuery.py . Essentially it first extracts all of the column 
and table names so that we can match them against nouns in the query. Then it builds a representation
of a graph for all of the relationships between different relations so that we can later
build joins to find the proper datatype for things like time or cities (ie. project future reservations by day).
"""

import psycopg2
import numpy as np

try:
    conn = psycopg2.connect("TOKENS WERE HERE")
except:
    print "I am unable to connect to the database"

cur = conn.cursor()

#get table names and column names
query_table_names="SELECT table_name \
  FROM information_schema.tables \
 WHERE table_schema='public' \
   AND table_type='BASE TABLE';"
cur.execute(query_table_names)
tables = cur.fetchall()
edges={}
columns={}
for i in range(len(tables)) :
    edges[tables[i][0]]=[]
    columns[tables[i][0]]=[]
    column_query="select column_name,data_type from information_schema.columns where table_name='"+tables[i][0]+"';"
    cur.execute(column_query)
    column_results = np.array( cur.fetchall() )
    for j in range(len(column_results)) :
        name=column_results[j][0]; type=column_results[j][1]
        if name=='zip' or name=='zip_code' :
            part='geo_zip'
        elif name=='city' :
            part='geo_city'
        elif name=='county' :
            part='geo_county'
        elif name=='state' :
            part='geo_state'
        elif 'timestamp' in type :
            part='time'
        else :
            part='other'
        columns[tables[i][0]].append( (name,part) )


#create graph edges based off of table foreign keys
for i in range(len(tables)) :
    s="SELECT DISTINCT \
        tc.constraint_name, tc.table_name, kcu.column_name, \
        ccu.table_name AS foreign_table_name, \
        ccu.column_name AS foreign_column_name \
    FROM \
        information_schema.table_constraints AS tc \
        JOIN information_schema.key_column_usage AS kcu \
          ON tc.constraint_name = kcu.constraint_name \
        JOIN information_schema.constraint_column_usage AS ccu \
          ON ccu.constraint_name = tc.constraint_name \
    WHERE constraint_type = 'FOREIGN KEY' AND tc.table_name='"+tables[i][0]+"'; "
    cur.execute(s)
    results = cur.fetchall()
    
    for j in range(len(results)) :
        edges[tables[i][0]].append( (results[j][3], results[j][2], results[j][4],'one-to-many') )
        edges[results[j][3]].append( (tables[i][0], results[j][2], results[j][4],'many-to-one') )


# save edge and column files to persistent storage
import pickle
output = open('table_info.pkl', 'wb')
pickle.dump(columns, output)
pickle.dump(edges, output)
output.close()







