Basic natural language analytics platform.

So basically the idea is you can make a natural language query about your data and then get back a graph or table containing the answer to your question.

Examples of queries:
Graph reservations by state in November.
Chart the cancelled reservations by users in California from March 1st-April 22nd 2014 and the second Saturday in November 2014 to the end of 2015.
Calculate the average user signups per day in the week before Christmas.
Predict the number of users who will sign up in the next month.
Predict the revenue from movies tomorrow in North Carolina.

The flow is / is the main page, which has components that are /part iframes and each of these /part pages is responsible for a single query. /query is an API endpoint to do the processing of a query and return the data to display and this is called by /part.

There are a bunch of really complicated ways to approach this problem, but there's a nice simplification because queries of this form follow a decently set form. They start with a verb (Show, graph, chart) then a noun phrase that contains information about the relation that they want information about and the chart type, then a bunch of prepositional phrases that act as modifiers (ie. in California, by month, in the next month). The processQuery.py script tries to parse all of this language into an internal representation then turn this internal representation into a postgres SQL query that can be run against a database.

TODO: A decent portion of the basic langauge parsing requirements are finished. Some of the more complicated relational language (ie. users who will sign up vs new users) still needs some work but about 80% of the tests are parsed into SQL correctly. The 20% that's missed don't need a complicated probabilistic model to solve-- just more cases to handle. Also a decent number of user queries are ambiguous, so gotta figure out some way to force users to give more information if the question is ambiguous.

As far as the prediction of information vs the display of existing information, there are a lot of services that can provide these predictions from decently arbitrary data (most of what people want to predict about user data is either solvable to a pretty high degree of accuracy with time series trends and/or collaborative filtering). Specific solutions for specific domains are always going to perform higher, but there's something to be said for getting a quick plug and play solution that's only 3% less accurate than a custom solution.

