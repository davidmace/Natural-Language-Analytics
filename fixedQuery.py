"""
This is an example demo of expected bahavior for the real system with the dynamic natural language processing.
This is called from the node backend /query2 API which runs this script in the background. This script reports
first the graph type then runs a postgres query against a company database to produce a table of results delimited
by the +=+ token.
"""

import sys
import psycopg2
import numpy as np

try:
    conn = psycopg2.connect("REAL TOKENS ARE HERE")
except:
    print "I am unable to connect to the database"

query=sys.argv[1]

def runquery(query) :
	cur = conn.cursor()
	cur.execute(q)
	results = np.array( cur.fetchall() )
	for result in results :
	    s=''
	    for val in result :
	        s+=str(val)+'+=+'
	    s=s.replace(',','')
	    print s[:-3]
	    
if query=='Show distribution of subscription life after free trials.' :
	print "xy-bubble"
	q="select t1.d, coalesce(t1.count,0), coalesce(t2.count,0) from \
	(select extract( day from now()-start_date) as d, count(*) \
	from subscriptions  \
	where free_trial_start_date<now() and start_date<now() and end_date>=start_date \
	group by d) as t1 \
	full join \
	(select extract( day from end_date-start_date) as d, count(*)  \
	from subscriptions  \
	where free_trial_start_date<now() and end_date<now() and end_date>=start_date  \
	group by d) as t2 \
	on t1.d=t2.d \
	order by t1.d;"
	runquery(query)

elif query=='Show distribution of reservations during free trials.' :
	print "xy"
	q="select ct, count(*) from ( \
	select count(*) as ct \
	from reservations \
	join subscriptions \
	on reservations.subscription_id=subscriptions.id \
	join subscription_events \
	on subscription_events.subscription_id=subscriptions.id \
	where subscription_events.action='startFreeTrial' and reservations.created_at<subscriptions.created_at+(INTERVAL '1 week' * 2) \
	group by subscriptions.id \
	) as t \
	group by ct \
	order by ct;"
	runquery(query)

elif query=='Show average subscription life after free trials.' :
	print "answer"
	q="select cast(sum(d*(c1+c2)) as bigint)/sum(c1+c2) from ( \
	select t1.d as d, coalesce(t1.count,0) as c1, coalesce(t2.count,0) as c2 from \
	(select extract( day from now()-start_date) as d, count(*) \
	from subscriptions  \
	where free_trial_start_date<now() and start_date<now() and end_date>=start_date \
	group by d) as t1 \
	full join \
	(select extract( day from end_date-start_date) as d, count(*) \
	from subscriptions \
	where free_trial_start_date<now() and end_date<now() and end_date>=start_date \
	group by d) as t2 \
	on t1.d=t2.d) as eh;"
	runquery(query)


	
elif query=='average reservations during free trials.' :
	print "answer"
	q="select (t1.n::float8)/(t2.n::float8) from \
	(select 0 as i, count(*) as n \
	from subscriptions \
	full join reservations \
	on reservations.subscription_id=subscriptions.id \
	where free_trial_start_date<now() and free_trial_end_date<now() and reservations.created_at<free_trial_end_date) as t1 \
	join \
	(select 0 as i, count(*) as n \
	from subscriptions \
	where free_trial_start_date<now() and free_trial_end_date<now()) as t2 \
	on t1.i=t2.i;"
	runquery(query)


elif query=='free trial conversion rate' :
	print "answer"
	q="select (t1.n::float8)/(t2.n::float8) from \
	(select 0 as i,count(*) as n \
	from subscriptions \
	where free_trial_start_date<now() and free_trial_end_date<now() and start_date<now()) as t1 \
	join \
	(select 0 as i, count(*) as n \
	from subscriptions \
	where free_trial_start_date<now() and free_trial_end_date<now()) as t2 \
	on t1.i=t2.i;"
	runquery(query)

elif query=='acquisition cost' :
	print "answer"
	q="select (t3.n::float8)/(t4.n::float8)/(t1.n::float8)*(t2.n::float8) from \
	(select 0 as i,count(*) as n \
	from subscriptions \
	where free_trial_start_date<now() and free_trial_end_date<now() and start_date<now()) as t1 \
	join \
	(select 0 as i, count(*) as n \
	from subscriptions \
	where free_trial_start_date<now() and free_trial_end_date<now()) as t2 \
	on t1.i=t2.i \
	join \
	(select 0 as i, count(*) as n \
	from subscriptions \
	full join reservations \
	on reservations.subscription_id=subscriptions.id \
	where free_trial_start_date<now() and free_trial_end_date<now() and reservations.created_at<free_trial_end_date) as t3 \
	on t1.i=t3.i \
	join \
	(select 0 as i, count(*) as n \
	from subscriptions \
	where free_trial_start_date<now() and free_trial_end_date<now()) as t4 \
	on t1.i=t4.i;"
	runquery(query)

#elif query=='Show average subscription life after free trials as a function of number of reservations during free trials.' :
#	print "answer"
#	q=""

else :
	print "unsupported"

