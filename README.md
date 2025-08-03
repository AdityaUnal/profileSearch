# Profile Searcher

- I have created a hybrid search retrieval system to find linkedIn profiles
- It filters based on hard-criterias(must haves) and soft-criterias(good to have)

## Getting Started
- Type the following commands in the terminal.
```
git clone https://github.com/AdityaUnal/profileSearch.git
pip install -r requirements.txt
```
- .env file
```
TURBOPUFFER_API_KEY=tpuf_xxxx
VOYAGE_API_KEY=pa-xxxx

```
## Steps 
- In detail steps that I had taken to work on this project are specified the [steps.md]() file.
- Additionally, the iterations that I tried are in the jobs_1 and jobs_2 jupyter notebooks.
## Result
- I got the following results for the .yml files.
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
<img width="2379" height="1180" alt="image" src="https://github.com/user-attachments/assets/64d03112-878e-4777-8142-dcc3b579deea" />
- The following image has been normalized between 0 and 1.
  <img width="2379" height="1180" alt="image" src="https://github.com/user-attachments/assets/bbdc2730-b6e5-47d6-bb5b-0ffa4ab0f1ac" />

