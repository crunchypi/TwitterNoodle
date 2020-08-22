# TwitterNoodle - Incident Detection using Twitter.

See the README folder for more extensive documentation. There should be a file called 'Documentation.pdf' - all functions and modules are described in the "All modules" section starting on page 10. Architecture overview (image) can be found on page 2.

<br/>

This project aims to detect incidents on micro-social media (Only twitter is supported) using a hierarchical storage and processing structure. The main functionality is storage in Neo4j and visualisation in a simple real-time front-end plot. Analysis can be found in root/Analysis.ipynb

## Requirements:
	(Twitter API keys)
	neo4j
	tweepy
	gensim
	textblob
	websockets
	matplotlib
	pandas
	wordcloud

# NOTE!
Update the root/credentials.py file, this project works with TwitterAPI and Neo4j most of the time and as such, keys are required.

## CLI in main.py:
The core interface is by using modular pipes to move and process the data. This CLI tool uses prefabs to make this easier. <br/>
Note: On first use, most pipes (those including a processing pipe) will use time to download and load a word2vec model; this might take a few minutes.
    
    Pipe tweets to local storage (pickle)
      -getdataset -ttime=10 -stime=10 -track=virus -path=./
    
    Pipe tweets from local storage (pickle) to Neo4j. Cleaning and processing pipes are used.
      -pipe=dsk2db -path=./...
    
    Pipe tweets from twitter directly to Neo4j. Cleaning and processing pipes are used.
      -pipe=api2db -track=to,and,from
  
    Pipe tweets from local storage (pickle) to front-end plot
      -pipe=dsk2js -path=./.. -query=help,me
    
    Pipe tweets from api to front-end plot. Cleaning and processing pipes are used.
      -pipe=api2js -track=to,and,from -query=help,me

    Divide a dataset in local storage (pickle)
      -scaledataset -sdiv=2 -sin=.. -sout=..
      
    Merge datasets in local storage (pickle)
       <implemented but not hooked to CLI>
       
## CLI in db_query.py:
This simple tool has a CLI menu system for browsing incidents in Neo4j.
