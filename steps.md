Here I have given a detailed report of the steps that I have followed to work on this project. 
Basically, the whats and whys of what I have done 

## Step 1 - Data Analysis

The data consists of the following :
- _id : UID for the object. It is unique
- personId and linkedinId : Indexed keys. Possibly unique.
- email : String object(Optional)
- experience : array of objects.One object consists of the following.
    - company 
    - positions : Array of objects.One object consists of the following.
        - title : string object 
        - startDate : String object.
        - endDate : 
        - description
        - yearsOfWorkExperience : Double object
    - yearsOfWorkExperience : Double object
    - prestige_score : double object
- yearsOfWorkExperience : Double object
- rerankSummary : string object.
- prestigeScore : Double object.
- skills : array of string
- awardsAndCertifications : array of objects. One object consists of the following.
    - type : string object.
    - name : string object.
    - confidence : double object.
- education : object consisting of the following.
    - highest_level : string object.
    - degrees : array of objects. One object consists of multiple string objects and prestige score which is a double object.
- country : string object.
- createdAt : date object.
- updatedAt : date object.
- headline : string object.
- profilepic : string object.

## Step 2 - Deploying and transferring to the Vector Store

- I am using Turbopuffer as it stores both vector index and inverted index. Inverted index might help with hard criteria.
- Deployed using docker.

## Step 3 - Possible Retrieval Strategies
- I went through different blogs and articles and could come up with a few ways to retrieve
- One thing that I tried was post and pre filtering.It has two issues :
    - Pre-filtering — filter by metadata first, then compute vector distances. Great recall (100%), but latency explodes (e.g. 10s).
    - Post-filtering — run ANN search, then discard results that don’t match the filter. Fast, but terrible recall (often 0%).


