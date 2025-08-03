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
- Deployed on cloud.

## Step 3 - Possible Retrieval Strategies
- First thing I tried was using BM25 algo for hard criterias. The top 100 that match these criterias would then go onto for top 10 ANN search for soft criteria.
    - These are the results across the different criterias :
      
    | Title                   | Average Score  | Average Soft Score     | Average Hard Score |
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
            - Profiles with low scores typically have mismatches in prestige, location, level of education.


- I did a few changes in my next trial.
    - Use spacy to identify the location of the university.The level of education can be checked by something similiar.
    - Used some hardcoded adjectives for description of work and education.
      
    | Title                   | Average Score | Average Soft Score    | Average Hard Score |
    |-------------------------|---------------|-----------------------|--------------------|
    | Tax Lawyer              | 80.67         | 7.5,8.2,8.5           | 1,1                |
    | Junior Corporate Laywer | 77            | 8.5,8.4,8.5           | 1,0.9              |
    | Radiology               | 63.3          | 5.3,8.75,8.15         | 0.8                |
    | Doctors (MD)            | 8.5           | 8.7,8.5               | 0.8,0.2,0.7        |
    | Biology Expert          | 39.5          | 8.15,8.9,7.3          | 0.7,0.6            | 
    | Anthropology            | 71.16         | 7.35,8.65,7.85        | 0.9,0.1            |
    | Mathematics PhD         | 69.5          | 8.95,8.35             | 0.9,0.8            |
    | Quantitative Finance    | 59.67         | 6.08,8.35,8.72        | 1,0.8              |
    | Bankers                 | 80.16         | 6.9,8.8,8.35          | 1,1                |
    | Mechanical Engineers    | 69            | 8.85,8.4,8.65         | 0.8,1              |
    - The hard score has significantly increased with only two criterias matching **less than 0.5** .
- I also tried giving some type of score to the BM25 retrieval so that the hard criteria has more say in the final ranking, but results were worse than both of these.
## Embedding Strategies
- I used VoyageAI to create embeddings of soft criteria.
