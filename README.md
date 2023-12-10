# Lisa Graph API Documentation
<div style="display:flex; align-items: center;width: 100%;">
  <img src="/assets/logo.png" alt="LISA GRAPH"/>
</div>
Lisa Graph, a robust Django-powered GraphQL API, facilitates seamless querying of Lusaka Stock Exchange data. The API offers a single query with optional filters (start, end, single_date, date) that fetches data in descending order by default.

## Getting Started

1. **Installation:**
   ```bash
   git clone https://github.com/suwilanji-chipofya-hadat/lisa_graph
   cd lisa_graph
   pip install -r requirements.txt
   make init # runs initial migrations (you can run individual commands in the makefile if you don't have make command available)
   make run # or
   python manage.py runserver
   ```

## NOTE: CHANGE THE DATABASE CONFIGURATIONS IN THE ```settings.py``` file
### WILL SOON PROVIDE ACCESS TO A PUBLIC DEVELOPMENT DATABASE
## Query

### Retrieve Data

```graphql
query {
  stockData(start: "2022-01-01", end: "2022-12-31", single_date: true, date: "2022-06-30") {
    # Fields to retrieve
    id
    name
    value
    date
  }
}
```

- **start (optional):** Start date for data filtering.
- **end (optional):** End date for data filtering.
- **single_date (optional):** Boolean flag for single-date retrieval.
- **date (optional):** Specific date for single-date retrieval.
#### IF NONE OF THE OPTIONAL PARAMETERS ARE PROVIDED THE API RETURNS ALL THE DATA
#### PAGINATION NOT YET SUPPORTED BUT WILL BE ADDED IN NO TIME

## Work Done

- ✔️ Implemented single GraphQL query.
- ✔️ Added optional date filters.
- ✔️ Data retrieval in descending order by default.
- ✔️ User authentication using JWT tokens.
## Future Work

- ☑️ Add support for news data from diffrent news platforms.
- ☑️ AI finance forecasts.
- ☑️ Blogging feature.
- ☑️ Forums.

### WOULD LOVE TO SEE YOUR PARTICIPATION IN THIS PROJECT
### FORK THE REPO AND ADD YOUR UPDATES WILL REVIEW AND ADD AS SOON AS POSSIBLE
