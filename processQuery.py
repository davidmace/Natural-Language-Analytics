import sys
import re
import numpy as np
import datetime

# TODO lots and lots of tests

query=sys.argv[1]

# prepositions to cut queries
timepreps=['before','after','between','since','on','in','during'] # during February
geopreps=['in'] # in California
branchpreps=['by'] # by state, by gender, by month
perpreps=['per']
otherpreps=['with','who','which','that'] # by state, by gender, by month
months=['','january','february','march','april','may','june','july','august','september','october','november','december'] #this first element is blank to map jan-->1, feb-->2
daysofweek=['mondays','tuesdays','wednesdays','thursdays','fridays','saturdays','sundays'] 
seasons=['spring','summer','fall','winter'] 
bygeo=['country','state','county','zip','city'] 
bytime=['year','season','month','day','day of week','day of year'] #TODO day of month should be added, and day should just mean split every day in range of multiple years


#stores all of the information that we want to pass about the query between functions
class QueryInfo:
    'data from the query'

    def __init__(self) :
        self.whereclauses=[]
        self.groupbys=[]
        self.noun=''
        self.order_by=''
        self.asc_or_desc=False
        self.num_results=0
        self.attr_modifier=''
        self.joins=[]
        self.modifiers=[]
        self.modifiertypes=[]
        self.verb=''
        self.find_what=''
        self.adj_list=[]
        self.perclauses=[]
        self.types_needed=[]
        self.object_phrase=[]
        self.joins=[]
        self.time_name=''
        self.attr_casts=[]
        self.map_of='USA'
        self.map_split=''
        self.time_split=''
        self.geo_available=[]
        self.geo_casts=[]
        self.intersects=[]

    def __str__(self):
        s=''
        s+='whereclauses: '+repr(self.whereclauses)+'\n'
        s+='groupbys: '+repr(self.groupbys)+'\n'
        s+='noun: '+self.noun+'\n'
        s+='order_by: '+self.order_by+'\n'
        s+='asc_or_desc: '+str(self.asc_or_desc)+'\n'
        s+='num_results: '+str(self.num_results)+'\n'
        s+='attr_modifier: '+self.attr_modifier+'\n'
        s+='joins: '+repr(self.joins)+'\n'
        s+='modifiers: '+repr(self.modifiers)+'\n'
        s+='modifiertypes: '+repr(self.modifiertypes)+'\n'
        s+='verb: '+self.verb+'\n'
        s+='find_what: '+self.find_what+'\n'
        s+='adj_list: '+repr(self.adj_list)+'\n'
        s+='perclauses: '+repr(self.perclauses)+'\n'
        s+='types_needed: '+repr(self.types_needed)+'\n'
        s+='object_phrase: '+repr(self.object_phrase)+'\n'
        s+='joins: '+repr(self.joins)+'\n'
        s+='time_name: '+self.time_name+'\n'
        s+='attr_casts: '+repr(self.attr_casts)+'\n'
        s+='map_of: '+self.map_of+'\n'
        s+='map_split: '+self.map_split+'\n'
        s+='time_split: '+self.time_split+'\n'
        s+='geo_available: '+repr(self.geo_available)+'\n'
        s+='geo_casts: '+repr(self.geo_casts)+'\n'
        s+='intersects: '+repr(self.intersects)+'\n'
        return s
    
    def __repr__(self):
        return str(self)


# intermediate representation of a date or time in the query
class QueryDate:
    'Stores info about a single date in a query'

    def __init__(self, year=-1, month=-1, day=-1, dayofweek=-1, season=-1):
        self.year=year
        self.month=month
        self.day=day
        self.dayofweek=dayofweek
        self.season=season
        
    def __str__(self):
        return str(self.day)+" "+str(self.month)+" "+str(self.year)+" "+str(self.dayofweek)+" "+str(self.season)
    
    def __repr__(self):
        return str(self)
    
    def convertToDay(self) :
        if self.day==-1 :
            self.day=1
        if self.month==-1 :
            self.month=1
            
    def dateString(self) :
        return str(self.year)+'-'+str(self.month)+'-'+str(self.day)
    

# if we want nov to feb then we do "or" around the end of the year, and otherwise we do "and" between the months' integer representations
def handleDateWrap(type, start, end) :
    if start<=end :
        return "EXTRACT( "+type+" FROM $datefield)>='"+str(start)+"' AND EXTRACT( "+type+" FROM $datefield)<'"+str(end)+"'"
    else :
        return "EXTRACT( "+type+" FROM $datefield)>='"+str(start)+"' OR EXTRACT( "+type+" FROM $datefield)<'"+str(end)+"'"
    

# seasons are 0-3 and months are 0-12
def convertSeasonToMonth(seasonid) :
    return str(seasonid*3)


# check if the given phrase matches any of the known date patterns
def match_date_scheme(scheme,modifier,i,span) :
    if i+span>len(modifier) :
        return False
    query=modifier[i:i+span]
    #print query
    for i in range(len(scheme)) :
        if scheme[i]==',' and query[i]!=',' :
            return False
        if scheme[i]=='/' and query[i]!='/' :
            return False
        if scheme[i]=='monthnum' or scheme[i]=='year' or scheme[i]=='day':
            try:
               val = int(query[i])
            except ValueError:
               return False
        if scheme[i]=='season' and (query[i] not in seasons) :
            return False
        if scheme[i]=='month' and (query[i] not in months) :
            return False
        if scheme[i]=='dayofweek' and (query[i] not in daysofweek) :
            return False
    return True;
        
        
# check a bunch of different date patterns by calling match_date_scheme for each 
# possibility starting at each word in the sentence
def parseTimeModifier(phrase) :

    #match all different types of dates
    dates=[]
    thiswhereclause=[]
    i=0
    while i<len(phrase) :
        if match_date_scheme( ['month','day',',','year'] , phrase, i, 4) :
            dates.append( QueryDate( month=months.index(phrase[i+0]), 
                day=int(phrase[i+1]), year=int(phrase[i+3]) ) )
            i+=4
        elif match_date_scheme( ['monthnum','/','day','/','year'] , phrase, i, 5 ) :
            dates.append( QueryDate( month=int(phrase[i+0]), 
                day=int(phrase[i+2]), year=int(phrase[i+4]) ) )
            i+=5
        elif match_date_scheme( ['month','year'] , phrase, i, 2 ) :
            dates.append( QueryDate( month=months.index(phrase[i+0]), year=int(phrase[i+1]) ) )
            i+=2
        elif match_date_scheme( ['season','year'] , phrase, i, 2 ) :
            dates.append( QueryDate( season=seasons.index(phrase[i+0]), year=int(phrase[i+1]) ) )
            i+=2
        elif match_date_scheme( ['year'] , phrase, i, 1 ) :
            dates.append( QueryDate( year=int(phrase[i+0]) ) )
            i+=1
        elif match_date_scheme( ['month'] , phrase, i, 1 ) :
            dates.append( QueryDate( month=months.index(phrase[i+0]) ) )
            i+=1
        elif match_date_scheme( ['season'] , phrase, i, 1 ) :
            dates.append( QueryDate( season=seasons.index(phrase[i+0]) ) )
            i+=1
        elif match_date_scheme( ['dayofweek'] , phrase, i, 1 ) :
            dates.append( QueryDate( dayofweek=daysofweek.index(phrase[i+0]) ) )
            i+=1
        else :
            i+=1

        
    # construct where clause from dates for each type of preposition 
    prep=phrase[0]
    if prep in ['on','in','during'] :
        for i in range(len(dates)) :
            clause=""
            if dates[i].year!=-1 :
                clause+=" EXTRACT(year FROM $datefield) = '"+str(dates[i].year)+"' AND"
            if dates[i].month!=-1 :
                clause+=" EXTRACT(month FROM $datefield) = '"+str(dates[i].month)+"' AND"
            if dates[i].day!=-1 :
                clause+=" EXTRACT(day FROM $datefield) = '"+str(dates[i].day)+"' AND"
            if dates[i].dayofweek!=-1 :
                clause+=" EXTRACT(dayofweek FROM $datefield) = '"+str(dates[i].dayofweek)+"' AND"
            if dates[i].season!=-1 :
                clause+=handleDateWrap( 'month', convertSeasonToMonth(dates[i].season),convertSeasonToMonth((dates[i].season+1)%4) )+" AND"
            clause=clause[:-4] # get rid of last 'and'
            thiswhereclause.append(clause)
    elif prep in ['after','since'] :
        if len(dates)!=1 :
            raise Exception("not 1 arg in after/since clause")
        dates[0].convertToDay()
        thiswhereclause.append( " $datefield > '"+dates[0].dateString()+"'" )

    elif prep in ['before'] :
        if len(dates)!=1 :
            raise Exception("not 1 arg in before clause")
        dates[0].convertToDay()
        thiswhereclause.append( " $datefield < '"+dates[0].dateString()+"'" )

    elif prep in ['between'] :
        if len(dates)!=2 :
            raise Exception("not 2 args in between clause")
        if dates[0].year!=-1 :   # assume simple range query if has year
            dates[0].convertToDay()
            dates[1].convertToDay()
            thiswhereclause.append( "$datefield >= '"+dates[0].dateString()+"' AND "+"$datefield < '"+dates[1].dateString()+"'" )
        else :
            if dates[0].month!=-1 :
                thiswhereclause.append( handleDateWrap('month', dates[0].month, dates[1].month) )
            elif dates[0].dayofweek!=-1 :
                thiswhereclause.append( handleDateWrap('dayofweek', dates[0].dayofweek, dates[1].daysofweek) )
            elif dates[0].season!=-1 :
                thiswhereclause.append( handleDateWrap('month', convertSeasonToMonth(dates[0].season), convertSeasonToMonth(dates[1].daysofweek)) ) 

    return thiswhereclause


#load geographical names so we can match them to query words
geo_info=np.loadtxt('scripts/geo_info.txt', dtype='S', delimiter=',')
for i in range(len(geo_info)) :
    geo_info[i]=np.array([name[1:-1].lower() for name in geo_info[i]])
zipnames=geo_info[:,0]
citynames=geo_info[:,3]
statenames=geo_info[:,4]
countynames=geo_info[:,5]


#load state abbreviations and make a mapping from abbreviation to state name so we can match
state_abbr=np.loadtxt('scripts/stateabbr.txt', dtype='S', delimiter=',')
state_abbr_dict=dict(zip(state_abbr[:,0], state_abbr[:,1]))
state_abbr_dict = {v.lower(): k.lower() for k, v in state_abbr_dict.items()}
#print state_abbr_dict


# get which granularity of geography for the word
def getGeoType(geoword) :
    if geoword in state_abbr_dict.keys() :
        istate=np.where( statenames==state_abbr_dict[geoword] )
        if len(istate[0])>0 :
            return 'state'
    icounty=np.where( countynames==geoword )
    if len(icounty[0])>0 :
        return 'county'
    icity=np.where( citynames==geoword )
    if len(icity[0])>0 :
        return 'city'
    #try :
    #    int(zip)
    #    return 'zip'
    #except ValueError :
    #    pass
    return None


# determine the word type for a given word
def getWordType(word) :
    geo=getGeoType(word)
    if geo is not None :
        return 'geo_'+geo
    try :
        int(word)
        return 'time'
    except ValueError :
        pass
    if word in bytime :
        return 'time'
    return word


# split query into prepositional phrases
def splitQueryIntoParts(queryInfo,s) :
    start=-1
    modifiers=[]
    words=s.replace('.','').replace(',',' , ').replace('/',' / ').split() # TODO handle .lower() here for non-valued entries
    for i in range(len(words)) :
        word=words[i]
        if (word in timepreps) or (word in geopreps) or (word in branchpreps) or (word in otherpreps) or (word in perpreps):
            if start==-1 :
                queryInfo.object_phrase=words[:i]
            else :
                queryInfo.modifiers.append(words[start:i])
            start=i
        if i==len(words)-1 :
            if start==-1 :
                queryInfo.object_phrase=words[:]
            else :
                queryInfo.modifiers.append(words[start:])
            start=i


# logic for determining type of phrase
def getModifierTypes(queryInfo) :
    queryInfo.modifiertypes=[]
    for i in range(len(queryInfo.modifiers)) : #loop phrases
        prep=queryInfo.modifiers[i][0]

        #handle intersection of time and geo prepositions
        if (prep in timepreps) and (prep in geopreps) :
            istime=False
            for word in queryInfo.modifiers[i][1:] :
                if (word in months) :
                    istime=True
                    break
                isint=True
                try:
                   val = int(word)
                except ValueError:
                   isint=False
                if isint :
                    istime=True
                    break
            if istime :
                queryInfo.modifiertypes.append('t')
            else :
                queryInfo.modifiertypes.append('g')

        elif prep in timepreps :
            queryInfo.modifiertypes.append('t')
        elif prep in geopreps :
            queryInfo.modifiertypes.append('g')
        elif prep in branchpreps :
            mod=' '.join(queryInfo.modifiers[i][1:])
            if mod in bytime :
                queryInfo.modifiertypes.append('bt')
            elif mod in bygeo :
                queryInfo.modifiertypes.append('bg')
            else :
                queryInfo.modifiertypes.append('bo')
        elif prep=='per' :
            queryInfo.modifiertypes.append('p')
        else :
            queryInfo.modifiertypes.append('o')


# parse adjectives attached to relation-referencing nouns
def parseModAttr(words, queryInfo, neg) :
    attr = words[0]
    value = ' '.join(words[2:])
    queryInfo.types_needed.append("column "+attr+" "+value.replace("\'","")+" "+str(neg))


# given a certain preposition we do various logic to place words from that phrase into
# slots in our final query representation
def extractInfoFromModifiers(queryInfo) :
    for j in range(len(queryInfo.modifiers)) :
        
        #extract dates from time modifiers
        phrase_unsplit=queryInfo.modifiers[j]
        modifier=' '.join(queryInfo.modifiers[j][1:])
        if queryInfo.modifiertypes[j]=='t' : #time
            queryInfo.whereclauses.append( parseTimeModifier(phrase_unsplit) ) #this should only happen once
            queryInfo.types_needed.append('time')
        elif queryInfo.modifiertypes[j]=='bg' : #by geo
            queryInfo.groupbys.append(modifier)
            queryInfo.types_needed.append('geo_'+modifier)
            queryInfo.map_split=modifier
        elif queryInfo.modifiertypes[j]=='bt' : # by time
            queryInfo.time_split=modifier
            if modifier=='day of week' :
                modifier='dow'
            elif modifier=='day of year' :
                modifier='doy'
            queryInfo.groupbys.append('EXTRACT( '+modifier+' FROM $datefield)' )
            queryInfo.types_needed.append('time')
        elif queryInfo.modifiertypes[j]=='bo' : # by other
            queryInfo.groupbys.append(modifier)
            queryInfo.types_needed.append(modifier)
        elif queryInfo.modifiertypes[j]=='g' : # geo
            queryInfo.types_needed.append('geo_'+getGeoType(modifier))
            queryInfo.map_of=modifier
            tokens = re.split('and |, ', modifier)
            tokens=[token.strip() for token in tokens]
            clause=[]
            for token in tokens :
                geotype=getGeoType(token)
                if geotype=='state' :
                    clause.append("LOWER("+geotype+") = '"+state_abbr_dict[token]+"'") #this cast to state abbr is sketchy
                else :
                    clause.append("LOWER("+geotype+") = '"+token+"'") #this cast to state abbr is sketchy
            queryInfo.whereclauses.append(clause)
        elif queryInfo.modifiertypes[j]=='p' : # per
            queryInfo.perclauses.append(modifier)
            queryInfo.types_needed.append(getWordType(modifier))
        elif queryInfo.modifiertypes[j]=='o' : # other
            parts = re.split('and |, ', modifier)
            parts=[part.strip() for part in parts]
            for part in parts :
                part = part.replace('=',' = ')
                neg=False
                if 'not' in part :
                    inot=part.find('not')
                    part=part[:inot]+part[inot+3:]
                    neg=True
                words=part.split()
                if 'is' in words or '=' in words :
                    parseModAttr(words, queryInfo, neg)
                else :
                    pass
                    #parseModDesc()




units = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]

tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

scales = ["hundred", "thousand", "million", "billion", "trillion"]

numwords={}
numwords["and"] = (1, 0)
for idx, word in enumerate(units):    numwords[word] = (1, idx)
for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)
                    
#convert string to int
def text2int(textnum):
    current = result = 0
    for i in range(len(textnum)):
        word=textnum[i]
        if word not in numwords:
          continue

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current


# we want to map specific words to word types in our internal representation
special_words={
#num
"zero":"num", "one":"num", "two":"num", "three":"num", "four":"num", "five":"num", "six":"num", "seven":"num", "eight":"num",
"nine":"num", "ten":"num", "eleven":"num", "twelve":"num", "thirteen":"num", "fourteen":"num", "fifteen":"num",
"sixteen":"num", "seventeen":"num", "eighteen":"num", 
"nineteen":"num","twenty":"num", "thirty":"num", "forty":"num", "fifty":"num", "sixty":"num", "seventy":"num", "eighty":"num", "ninety":"num", 
"hundred":"num", "thousand":"num", "million":"num", "billion":"num", "trillion":"num",

#ignore
"the":"ignore", "all":"ignore", "total":"ignore",

#most
'most':'most','biggest':'most','best':'most','highest':'most','largest':'most','max':'most','maximum':'most','greatest':'most', 

#least
'least':'least','smallest':'least','worst':'least','lowest':'least','min':'least','minimum':'least',

#average
'average':'average', 'mean':'average',

#by time
'daily':'time', 'hourly':'time', 'monthly':'time', 'yearly':'time'

}


# simple util to error check parsing int
def extractint(s) :
    for word in s :
        try:
            val = int(word)
            return val
        except ValueError:
           pass


# parse start of phrase which contain noun, verb, type of graph
def parseDescriptors(queryInfo) :
    queryInfo.verb = queryInfo.object_phrase[0]
    queryInfo.noun = queryInfo.object_phrase[-1]
    queryInfo.object_phrase = queryInfo.object_phrase[1:-1]
    
    # example "show a graph of reservations"
    of_split=np.where(np.array(queryInfo.object_phrase)=='of')[0]
    find_what=''
    if len(of_split)>0 :
        queryInfo.find_what=queryInfo.object_phrase[:of_split[0]]
        queryInfo.object_phrase=queryInfo.object_phrase[of_split[0]+1:]
    #print [find_what]
    
    queryInfo.adj_list+=queryInfo.object_phrase
    
    word_types=[]
    for word in queryInfo.adj_list :
        word_type='other'
        if word in special_words.keys() :
            word_type=special_words[word]
        try :
            int(word)
            word_type='num'
        except ValueError:
           pass
        word_types.append( word_type )
    #print word_types
    
    num_results=text2int(queryInfo.adj_list) #assumes there is at most one number
    if queryInfo.num_results==0 :
        queryInfo.num_results=extractint(queryInfo.adj_list)
        
    # example "show the most viewed movie"
    queryInfo.asc_or_desc=True
    queryInfo.order_by=''
    if 'most' in word_types :
        queryInfo.order_by=queryInfo.adj_list[ word_types.index('most')+1 ]
        queryInfo.asc_or_desc=False
    elif 'least' in word_types :
        queryInfo.order_by=queryInfo.adj_list[ word_types.index('least')+1 ]
        queryInfo.asc_or_desc=True
    
    # handle what we want to extract from the relation (ie. count(distinct *))
    queryInfo.attr_modifier='count(*)'
    #attr_modifier='sum($attr)'
    #if 'average' in word_types :
    #    attr_modifier='avg($attr)'
    if len(queryInfo.perclauses)>0 :
        queryInfo.attr_modifier+='/count(DISTINCT '
        if queryInfo.perclauses[0] in bytime :
            queryInfo.attr_modifier+='EXTRACT('+queryInfo.perclauses[0]+' FROM $datefield) '
        else :
            queryInfo.attr_modifier+=queryInfo.perclauses[0]
        queryInfo.attr_modifier+=')'
        queryInfo.types_needed.append(getWordType(queryInfo.perclauses[0]))
            
    # handle parsing of time delimiting phrases
    if 'time' in word_types :
        mod=queryInfo.adj_list[ word_types.index('time') ]
        transition={'hourly':'hour','daily':'day','weekly':'week','monthly':'month','yearly':'year'}
        queryInfo.groupbys.append( 'EXTRACT('+transition[mod]+' FROM $datefield)' )
        queryInfo.types_needed.append('time')
        
    #if we have other random conditions just append another special where
    for i in range(len(word_types)) :
        if word_types[i]=='other' :
            queryInfo.whereclauses.append(['$attr='+queryInfo.adj_list[i]])
            queryInfo.types_needed.append(queryInfo.adj_list[i])
            

#print 'yo1'

import psycopg2
import numpy as np



try:
    conn = psycopg2.connect("DATABASE TOKENS")
except:
    print "I am unable to connect to the database"



cur = conn.cursor()

#load the precomputed information about the database
import pprint, pickle
pkl_file = open('table_info.pkl', 'rb')
columns = pickle.load(pkl_file)
edges = pickle.load(pkl_file)
pkl_file.close()



import Queue

# This is decently complex. Do BFS on the relationships between different relations in our database.
# We have different types of information that our query tells us to look for in our database (ie. geo or time)
# so we use the heuristic of finding the shortest path in the tree of relationships to an attribute of that
# type. We start the search at the noun in the query sentence, which refers to a relation.

def findAttrInTree(searchfor, queryInfo, edges, columns) :
    #print searchfor
    queue=Queue.Queue()
    visitednodes={}
    parentnodes={queryInfo.noun:'None'}
    fieldname=''; column_attr=''; not_value=False
    queue.put(queryInfo.noun)
    while not queue.empty() :
        curtable=queue.get()
        #print curtable

        # look at this specific relation for the correct column
        visitednodes[curtable]=1
        for column in columns[curtable] :
            name=column[0]; part=column[1]
            if searchfor=='time' and part=='time' :
                fieldname=curtable+'.'+name
                break # breaks while loop
            if 'geo' in searchfor and 'geo' in part :
                fieldname=curtable+'.'+name
                break # breaks while loop
            #print searchfor[:len('column')], searchfor.split()[1]
            if searchfor[:len('column')]=='column' and name==searchfor.split()[1] :
                column_attr=searchfor.split()[2]
                not_value=searchfor.split()[3]
                fieldname=curtable+'.'+name
                #print fieldname
                break
            #TODO handle adjectives (ie. cancelled)
        else : # we haven't found the goal so we keep going
            for edge in edges[curtable] :
                next=edge[0]; attr1=edge[1]; attr2=edge[2]; edge_direction=edge[3]
                if next in visitednodes.keys() :
                    continue
                queue.put( (next) )
                parentnodes[next]=(curtable,attr1,attr2,edge_direction)
            continue # if we got into this else, then we didn't break earlier so we continue
        break
        
    #if type is geo then extract all the geo types from the destination node
    for column in columns[curtable] :
        for i in range(len(bygeo)) :
            if column[0]==bygeo[i] :
                queryInfo.geo_available[i]=1

    #trace back path to destination node and join on those edges
    contains_n_to_one=False
    tracetable=curtable
    thisjoins=[]
    for i in range(10) :
        if tracetable is queryInfo.noun :
            break
        transition=parentnodes[tracetable]
        thisjoins.append( 'join '+tracetable+' on '+transition[0]+'.'+transition[2]+'='+tracetable+'.'+transition[1] )
        #print transition
        edge_direction=transition[3]
        #print edge_direction
        if edge_direction=='many-to-one' :
            contains_n_to_one=True
        tracetable=transition[0]
    thisjoins=list(reversed(thisjoins))

    #add an intersect group if there is a many-to-one in the edge path
    if contains_n_to_one and searchfor[:len('column')]=='column':
        queryInfo.intersects.append( (tracetable,transition[1],transition[2],fieldname,column_attr,thisjoins,not_value) )

    queryInfo.joins.extend( thisjoins )

    return fieldname


            
# sometimes we can find cities in the table but the query asks for states so we can cast up to less precision
def addGeoCast(queryInfo) :
    if queryInfo.map_split=='' :
        return
    wantgeo=bygeo.index( queryInfo.map_split )
    havegeo=wantgeo
    while havegeo<5 :
        if queryInfo.geo_available[havegeo]==1:
            break
        havegeo+=1
    if wantgeo!=havegeo :
        queryInfo.attr_casts.append([ bygeo[wantgeo], bygeo[havegeo] ])
        for i in range(len(queryInfo.groupbys)) :
            if queryInfo.groupbys[i]==bygeo[wantgeo] :
                queryInfo.groupbys[i]=bygeo[havegeo]
                break


# all of the above code builds up an internal representation of the query given the relations we
# have in the database. Now we need to write that into a postgres query.
def makeQueryString(queryInfo) :
    query='SELECT '
    for group in queryInfo.groupbys :
        query+=group+","
    query+=queryInfo.attr_modifier
    query+=' FROM '+queryInfo.noun+' '
    queryInfo.joins=list(set(queryInfo.joins))
    for join in queryInfo.joins :
        query+=join+' '
    if len(queryInfo.intersects)>0 : # TODO need to handle when intersects are from different relations ie. multiple join tables
        query+='join ( '
        for intersect in queryInfo.intersects :
            query+='select '+intersect[1]+' from '+intersect[0]+' '
            for join in intersect[5] :
                query+=join+' '
            query+=' where '+intersect[3]
            query+='!=' if intersect[6]=="True" else '='
            query+="\'"+intersect[4]+"\'"
            query+=' intersect '
        query=query[:-len(' intersect ')]
        query+=' ) as t'
        query+=' on t.'+intersect[1]+'='+intersect[0]+'.'+intersect[2]
    #print queryInfo.whereclauses
    if len(queryInfo.whereclauses)>0 :
        query+=' WHERE'
        for i in range(len(queryInfo.whereclauses)) :
            query+=' '+queryInfo.whereclauses[i][0] #TODO add multiple queries for where branches
            if i<len(queryInfo.whereclauses)-1 :
                query+=' AND'
    if len(queryInfo.groupbys)>0 :
        query+=' GROUP BY '
        for group in queryInfo.groupbys :
            query+=group+","
        query=query[:-1]
    if queryInfo.order_by is not '' :
        query+= ' ORDER BY '+queryInfo.order_by
        if queryInfo.asc_or_desc==True :
            query+=' ASC'
        else :
            query+=' DESC'
    elif queryInfo.groupbys :
        query+=' ORDER BY '
        for group in queryInfo.groupbys :
            query+=group+","
        query=query[:-1]
    if queryInfo.num_results is not None :
        query+=' LIMIT '+str(queryInfo.num_results)
    query=query.replace('$datefield',queryInfo.time_name)
    #print query
    return query



def queryToSQL(s) :
    queryInfo = QueryInfo()

    # get modifier phrases
    splitQueryIntoParts(queryInfo,s)
    
    # get modifier type
    getModifierTypes(queryInfo)

    #handle date modifiers
    extractInfoFromModifiers(queryInfo)

    #break down main clause
    parseDescriptors(queryInfo)

    #print queryInfo
    
    #figure out what geo tiers are available in the database
    queryInfo.geo_available=np.zeros(5)
    queryInfo.time_name=''
    for i in range(len(queryInfo.types_needed)) :
        if 'geo' in queryInfo.types_needed[i] :
            queryInfo.types_needed[i]='geo'
    queryInfo.types_needed = list(set(queryInfo.types_needed))
    queryInfo.joins=[]
    for type in queryInfo.types_needed :
        name = findAttrInTree(type, queryInfo, edges, columns)
        if type is 'time' :
            queryInfo.time_name=name

        #if type[:3] is 'geo' :
    #queryInfo.geo_available[3]=1; queryInfo.geo_available[4]=1 #TEMP
    
    addGeoCast(queryInfo)
    #print queryInfo

    #make sql queries
    query=makeQueryString(queryInfo)

    return [query,queryInfo]       
    
            

### Data Display Logic

#if there is a geo dimsension and time dimension :
#    graph a animated heat map
#elif there is a geo dimension and another dimension:
#    graph a 1xn matrix of heat maps
#elif there is a geo dimension :
#    graph a heat map
#elif there are 3 dimensions and at least one is numeric :
#    make a 2D heat plot
#elif there are 2 dimensions and both are numeric:
#    make a graph
#elif there are 2 dimensions or smaller :
#    make a table


def getGroupByType(result_column) :
    try :
        float(result_column[0])
    except ValueError :
        return 'text'
    return 'num'

# find type of graph we need for representing this form of data
def getResultType(results,queryInfo) :
    numresults=results.shape[0]
    numdimensions=results.shape[1]
    groupbytypes=[getGroupByType(results[:,i]) for i in range(len(queryInfo.groupbys))] #TODO this is repetitive
    groupbytypes.append(getGroupByType(results[:,-1]))
    nmap_of = state_abbr_dict[queryInfo.map_of] if queryInfo.map_of in state_abbr_dict else queryInfo.map_of
    if 'bg' in queryInfo.modifiertypes and 'bt' in queryInfo.modifiertypes :
        return 'animatedMap,'+nmap_of+','+queryInfo.map_split
    elif 'bg' in queryInfo.modifiertypes and numdimensions>=3 :
        return 'mapArray,'+nmap_of+','+queryInfo.map_split
    elif 'bg' in queryInfo.modifiertypes and numdimensions>=2 :
        return 'map,'+nmap_of+','+queryInfo.map_split
    elif numdimensions==3 and 'num' in groupbytypes :
        return 'heatplot'
    elif numdimensions==2 and 'num' in groupbytypes:
        return 'chart'
    #elif numdimensions==2 and groupbytypes[0]=='num' and groupbytypes[1]=='num' :
    #    return 'scatter'
    #elif numdimensions==2 : #and groupbytypes[0]=='num' and groupbytypes[1]=='num' :
    #    return 'bar'
    return 'table'
        
# name the columns of our graphs that we're producing
def nameTimeValues(result,queryInfo) :
    nresult=[]
    for i in range(len(queryInfo.groupbys)) :
        if queryInfo.modifiertypes[i]=='bt' :
            if queryInfo.time_split=='year' or queryInfo.time_split=='day' :
                nresult.append(result[i])
            elif queryInfo.time_split=='day of year' : #TODO there should be an error with leap years here
                date = datetime.datetime(2000, 1, 1) + datetime.timedelta(int(result[i]) - 1)
                nresult.append(months[date.month][:3]+' '+str(date.day))
            elif queryInfo.time_split=='day of week' :
                nresult.append( daysofweek[int(result[i])] )
            elif queryInfo.time_split=='month' : #TODO there should be an error with leap years here
                nresult.append( months[int(result[i])] )
        else :
            nresult.append(result[i])
    nresult.append(result[-1]) # account for val field that isn't a groupby
    return nresult


# we find the largest granularity of geography in our data that is lower than the one we want
def castGeo(results, queryInfo) :
    if len(queryInfo.attr_casts)==0 :
        return results
    [geo_wanted,geo_available]=queryInfo.attr_casts[0]
    array_locations={'zip':0, 'city':3, 'county':5, 'state':4}
    search_column=array_locations[geo_available]
    answer_column=array_locations[geo_wanted]
    
    nvals={}
    for i in range(len(results)) :
        [group,val]=results[i] 
        found=np.where( geo_info[:,search_column]==group )[0] 
        if len(found)==0 :
            continue
        row=found[0] #only need to find first occurence since casting down in specificity
        answer=geo_info[row,answer_column]

        #handle when there are mulitple city/county with same name in different states
        prefix=''
        if queryInfo.map_of=='USA' :
            prefix=geo_info[row,4]
            answer=prefix+' '+answer
        if answer not in nvals :
            nvals[answer]=int(val)
        else :
            nvals[answer]+=int(val)
    return np.array(nvals.items(), dtype='S')



# convert query to SQL representation. The magic.
[sqlquery,queryInfo] = queryToSQL(query);

# run query and pass results and chart metainfo back to nodejs /part
cur.execute(sqlquery)
results = np.array( cur.fetchall() )
results=castGeo(results,queryInfo)
print getResultType(results,queryInfo)
for result in results :
    result=nameTimeValues(result,queryInfo)
    s=''
    for val in result :
        s+=str(val)+'+=+'
    print s[:-3]
    

#print findAttrInTree('column_action', queryInfo, edges, columns)



