Geographic Resource
==================

The Geographic resource provides access to geographic subdivisions (states, provinces, counties, districts) for countries worldwide. This API leverages the `pycountry` library to provide standardized geographic data.

.. _Geographic_Base_URL:

Base URL
--------

The geographic routes are available at:

    - http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema

.. _Geographic_Overview:

Overview
--------

The geographic API provides access to administrative subdivisions for countries. It supports two levels of subdivisions:

- **Level 1**: States, provinces, or equivalent first-level administrative divisions
- **Level 2**: Counties, districts, or equivalent second-level administrative divisions

+------------------+--------------------+----------------------------------------+
| Resource         | Action             | Description                            |
+==================+====================+========================================+
| geographic       | subdivisions_schema| Geographic subdivisions for countries  |
+------------------+--------------------+----------------------------------------+

.. _Geographic_Parameters:

Parameters
----------

The geographic API accepts the following request parameters:

+-----------------+-----------------------+-------------------------------------------------------------------------+
| Key             | Value                 | Description                                                             |
+=================+=======================+=========================================================================+
| country         | ISO 3166-1 alpha-2    | Filter subdivisions by country code (e.g., "US", "ES", "DE")           |
|                 | country code          | If not provided, returns subdivisions from all countries               |
+-----------------+-----------------------+-------------------------------------------------------------------------+
| depth           | 0, 1, 2, or negative  | Filter by subdivision depth level                                       |
|                 |                       | - 0 or omitted: Returns all depths (both 1 and 2)                      |
|                 |                       | - 1: Returns only level 1 subdivisions (states/provinces)              |
|                 |                       | - 2: Returns only level 2 subdivisions (counties/districts)            |
|                 |                       | - Negative values: Returns all depths (same as 0)                      |
+-----------------+-----------------------+-------------------------------------------------------------------------+

.. _Geographic_Usage_Examples:

Usage Examples
--------------

Get all subdivisions from all countries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns all subdivisions at all depths from all countries:

    - http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema

.. code-block:: javascript

    {
        count: 15000,
        items: [
            {
                code: "US-CA",
                name: "California",
                type: "state",
                country_code: "US",
                parent_code: "US",
                parent: "United States",
                depth: 1
            },
            {
                code: "US-CA-001",
                name: "Alameda County",
                type: "county",
                country_code: "US",
                parent_code: "US-CA",
                parent: "California",
                depth: 2
            }
        ],
        depth: 0,
        _runtime: 0.123
    }

Get subdivisions for a specific country
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns all subdivisions for Spain:

    - http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema?country=ES

.. code-block:: javascript

    {
        count: 52,
        items: [
            {
                code: "ES-M",
                name: "Madrid",
                type: "province",
                country_code: "ES",
                parent_code: "ES",
                parent: "Spain",
                depth: 1
            }
        ],
        country: "ES",
        depth: 0,
        _runtime: 0.045
    }

Get level 1 subdivisions only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns only states/provinces for the United States:

    - http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema?country=US&depth=1

.. code-block:: javascript

    {
        count: 50,
        items: [
            {
                code: "US-CA",
                name: "California",
                type: "state",
                country_code: "US",
                parent_code: "US",
                parent: "United States",
                depth: 1
            }
        ],
        country: "US",
        depth: 1,
        _runtime: 0.032
    }

Get level 2 subdivisions only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns only counties/districts for Germany:

    - http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema?country=DE&depth=2

.. code-block:: javascript

    {
        count: 401,
        items: [
            {
                code: "DE-BB-BAR",
                name: "Barnim",
                type: "rural district",
                country_code: "DE",
                parent_code: "DE-BB",
                parent: "Brandenburg",
                depth: 2
            }
        ],
        country: "DE",
        depth: 2,
        _runtime: 0.078
    }

Get all subdivisions at a specific depth (no country filter)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns all level 1 subdivisions from all countries:

    - http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema?depth=1

.. code-block:: javascript

    {
        count: 2500,
        items: [
            {
                code: "US-CA",
                name: "California",
                type: "state",
                country_code: "US",
                parent_code: "US",
                parent: "United States",
                depth: 1
            },
            {
                code: "ES-M",
                name: "Madrid",
                type: "province",
                country_code: "ES",
                parent_code: "ES",
                parent: "Spain",
                depth: 1
            }
        ],
        depth: 1,
        _runtime: 0.156
    }

Error handling
~~~~~~~~~~~~~

When requesting subdivisions for a non-existent country:

    - http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema?country=XX

.. code-block:: javascript

    {
        count: 0,
        items: [],
        error: "Country not found: XX",
        depth: 0,
        _runtime: 0.012
    }

.. _Geographic_Response_Format:

Response Format
--------------

The geographic API returns a standardized response format:

.. code-block:: javascript

    {
        count: 52,                    // Number of subdivisions found
        items: [                      // Array of subdivision objects
            {
                code: "ES-M",         // ISO 3166-2 subdivision code
                name: "Madrid",       // Human-readable subdivision name
                type: "province",     // Type of administrative division
                country_code: "ES",   // ISO 3166-1 alpha-2 country code
                parent_code: "ES",    // Parent subdivision or country code
                parent: "Spain",      // Human-readable parent name
                depth: 1              // Administrative level (1 or 2)
            }
        ],
        country: "ES",                // Requested country code (if specified)
        depth: 1,                     // Requested depth level (if specified)
        error: "Error message",       // Error message (if applicable)
        _runtime: 0.045               // Request processing time in seconds
    }

**count**
    The number of subdivisions found matching the criteria

**items**
    Array of subdivision objects with the following fields:

    - **code**: ISO 3166-2 subdivision code (e.g., "US-CA", "ES-M")
    - **name**: Human-readable subdivision name
    - **type**: Type of administrative division (e.g., "state", "province", "county")
    - **country_code**: ISO 3166-1 alpha-2 country code
    - **parent_code**: Code of the parent subdivision or country
    - **parent**: Human-readable name of the parent subdivision or country
    - **depth**: Administrative level (1 for states/provinces, 2 for counties/districts)

**country**
    The country code that was requested (only present when country parameter is used)

**depth**
    The depth level that was requested (only present when depth parameter is used)

**error**
    Error message when the request cannot be fulfilled (e.g., country not found)

**_runtime**
    The time in seconds needed to process the request

.. _Geographic_Data_Sources:

Data Sources
-----------

The geographic data is sourced from the `pycountry` library, which provides:

- **ISO 3166-1**: Country codes and names
- **ISO 3166-2**: Subdivision codes and names
- **Standardized naming**: Consistent naming conventions across countries
- **Regular updates**: Updated subdivision data as administrative boundaries change

.. _Geographic_Authentication:

Authentication
-------------

The geographic API endpoints are **publicly accessible** and do not require authentication. This allows for easy integration with frontend applications and external systems that need geographic data.

.. _Geographic_Performance:

Performance Considerations
-------------------------

- **Caching**: Geographic data is relatively static and can be cached effectively
- **Large datasets**: Some countries have many subdivisions (e.g., US has ~3,000 counties)
- **Filtering**: Use country and depth parameters to limit results and improve performance
- **Response time**: Typical response times are under 100ms for filtered queries

.. _Geographic_Integration:

Integration Examples
-------------------

JavaScript example for populating a state dropdown:

.. code-block:: javascript

    fetch('/senaite/@@API/senaite/v1/geographic/subdivisions_schema?country=US&depth=1')
        .then(response => response.json())
        .then(data => {
            const stateSelect = document.getElementById('state');
            data.items.forEach(state => {
                const option = document.createElement('option');
                option.value = state.code;
                option.textContent = state.name;
                stateSelect.appendChild(option);
            });
        });

Python example for getting subdivisions:

.. code-block:: python

    import requests
    
    def get_country_subdivisions(country_code, depth=0):
        url = f"http://localhost:8080/senaite/@@API/senaite/v1/geographic/subdivisions_schema"
        params = {"country": country_code, "depth": depth}
        response = requests.get(url, params=params)
        return response.json()
    
    # Get all Spanish provinces
    spain_provinces = get_country_subdivisions("ES", depth=1)
    print(f"Spain has {spain_provinces['count']} provinces") 