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
### First thing I tried was using BM25 algo for hard criterias. The top 100 that match these criterias would then go onto for top 10 ANN search for soft criteria.
- These are the results across the different criterias : 
 | Title                  | Average Score | Average Soft Score    | Average Hard Score |
|-------------------------|---------------|-----------------------|--------------------|
| Tax Lawyer              | 78            | 8.1,8.1,7.2           | 1,1                |
| Junior Corporate Laywer | 74.67         | 8.25,8.35,8.2         | 1,0.9              |
| Radiology               | 69.7          | 4.8,8.15,7.95         | 1                  |
| Doctors (MD)            | 7.5           | 7.1,7.5               | 0.2,0.1,0.5        |
| Biology Expert          | 0             | 8.2,8.8,6.9           | 0.1,0.2            | 
| Anthropology            | 31            | 7.3,8.5,7.6           | 0.4,1              |
| Mathematics PhD         | 8.5           | 8.8,8.1               | 0.5,0.3            |
| Quantitative Finance    | 9             | 6.08,8.35,8.72        | 0.9,0.1            |
| Bankers                 | 54            | 7.3,8.5,8             | 1,0.7              |
| Mechanical Engineers    | 86.5          | 9,8.45,8.5            | 1,1                |
- The evaluation endpoint was helpful in finding the problems.
    - The soft criteria mostly have good scores.
    - Ignoring a few exceptions the hard scores are low.I believe this is due to the following reasons :
        - Filtering first on the basis of hard criteria. Then going to the soft criterias, this way even the profiles matching better on the hard criteria were push down.
        - Profiles with low scores typically have mismatches in prestige, location, level of 


